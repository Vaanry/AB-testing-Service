import numpy as np
from pydantic import BaseModel
from scipy import stats

class MetricsService:
    def __init__(self, data_service):
        self.data_service = data_service

    def _get_data_subset(self, table_name, begin_date, end_date, user_ids=None, columns=None):
        return self.data_service.get_data_subset(table_name, begin_date, end_date, user_ids, columns)

    def _calculate_response_time(self, begin_date, end_date, user_ids):
        df = self._get_data_subset('web-logs', begin_date, end_date, user_ids, ['user_id', 'load_time'])
        df = df.rename(columns={'load_time':'metric'})
        return df

    def _calculate_revenue_web(self, begin_date, end_date, user_ids):
        users = self._get_data_subset('web-logs', begin_date, end_date, user_ids).user_id.unique()
        sales = self._get_data_subset('sales',  begin_date, end_date, user_ids, ['user_id', 'price'])

        sales = sales[sales['user_id'].isin(users)]
        sales = sales.groupby('user_id', as_index=False).agg({'price':'sum'}).\
                rename(columns={'price':'metric'})
        df = pd.merge(pd.DataFrame({'user_id': users}), sales, on='user_id', how='left').fillna(0)
        return df        

    def _calculate_revenue_all(self, begin_date, end_date, user_ids):
        users = self._get_data_subset('web-logs', None, end_date, user_ids).user_id.unique()
        sales = self._get_data_subset('sales',  begin_date, end_date, user_ids, ['user_id', 'price'])

        sales = sales[sales['user_id'].isin(users)]
        sales = sales.groupby('user_id', as_index=False).agg({'price':'sum'}).\
                rename(columns={'price':'metric'})
        df = pd.merge(pd.DataFrame({'user_id': users}), sales, on='user_id', how='left').fillna(0)
        return df        
        
    def _calculate_cuped(self, df):
        metric = df['metric'].values
        cov = df['cov'].values
        theta = self.calculate_theta(metric, cov)
        return df['metric'] - theta * (df['cov'] - df['cov'].mean())

    def calculate_metric(self, metric_name, begin_date, end_date, cuped, user_ids=None):
        if metric_name == 'revenue (web)':
            if cuped == 'off':
                return self._calculate_revenue_web(begin_date, end_date, user_ids)
            elif cuped == 'on (previous week revenue)':
                df = self._calculate_revenue_web(begin_date, end_date, user_ids)                   
                cov_begin = begin_date-timedelta(days=7)                
                df_cov = (
                    self._calculate_revenue_web(cov_begin, begin_date, user_ids)
                    .rename(columns={'metric': 'cov'})
                )
                df = pd.merge(df, df_cov, on='user_id', how='left').fillna(0)
                df['metric'] = self._calculate_cuped(df)
                return df[['user_id', 'metric']]                       
            else:
                raise ValueError('Wrong cuped')
        else:
            raise ValueError('Wrong metric name')
    
    @staticmethod
    def calculate_theta(metric, cov):        
        covariance = np.cov(cov, metric)[0, 1]
        variance = cov.var()
        theta = covariance / variance
        return theta
    
    def process_outliers(self, metrics, design):
        metrics = metrics.copy()        
        lower = design.metric_outlier_lower_bound
        upper = design.metric_outlier_upper_bound
        if design.metric_outlier_process_type == 'drop':
            metrics = metrics[(metrics['metric']>lower)&(metrics['metric']<upper)]
        elif design.metric_outlier_process_type == 'clip':
            metrics.loc[metrics['metric'] < lower, 'metric'] = lower
            metrics.loc[metrics['metric'] > upper, 'metric'] = upper
        else:
            raise ValueError('Неверный способ обработки выбросов!')
        return metrics
    
    def calculate_linearized_metrics(
        self, control_metrics, pilot_metrics, control_user_ids=None, pilot_user_ids=None):   
        stat_a = control_metrics.groupby('user_id')['metric'].agg(['sum', 'count'])  
        stat_b = pilot_metrics.groupby('user_id')['metric'].agg(['sum', 'count'])        
        if control_user_ids:
            control_users = pd.DataFrame(control_user_ids, columns=['user_id'])
            stat_a = control_users.merge(stat_a, on='user_id', how='left').fillna(0)                    
        if pilot_user_ids:
            pilot_users = pd.DataFrame(pilot_user_ids, columns=['user_id'])
            stat_b = pilot_users.merge(stat_b, on='user_id', how='left').fillna(0)             
        sum_a, count_a = stat_a.sum()
        sum_b, count_b = stat_b.sum()        
        kappa = sum_a / count_a        
        lin_control = stat_a['sum'] - kappa * stat_a['count']
        lin_pilot = stat_b['sum'] - kappa * stat_b['count']        
        lin_control_metrics = pd.DataFrame(lin_control, columns=['metric']).reset_index()
        lin_pilot_metrics = pd.DataFrame(lin_pilot, columns=['metric']).reset_index()       
        return lin_control_metrics, lin_pilot_metrics