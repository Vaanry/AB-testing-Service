import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats

class ExperimentsService:
    def get_pvalue(self, metrics_a_group, metrics_b_group, design):
        if design.statistical_test == 'ttest':
            return stats.ttest_ind(metrics_a_group, metrics_b_group).pvalue
        else:
            raise ValueError('Неверный design.statistical_test')
    
    def estimate_sample_size(self, metrics, design):
        std = np.std(metrics['metric'].values)
        mu = np.mean(metrics['metric'].values)
        epsilon = design.effect / 100 * mu        
        n_users = metrics.user_id.nunique()
        n_metrics = metrics.metric.shape[0]
        ratio = n_users / n_metrics        
        sample_size = self.get_sample_size_abs(epsilon, std, design.alpha, design.beta, ratio)            
        return sample_size
        
    @staticmethod
    def get_sample_size_abs(epsilon, std, alpha, beta, ratio):
        t_alpha = norm.ppf(1 - alpha / 2, loc=0, scale=1)
        t_beta = norm.ppf(1 - beta, loc=0, scale=1)
        z_scores_sum_squared = (t_alpha + t_beta) ** 2
        sample_size = int(
            np.ceil(
                z_scores_sum_squared * (2 * std ** 2) / (epsilon ** 2) * ratio
            )
        )
        return sample_size
        
    def _create_group_generator(self, metrics, sample_size, n_iter):
        user_ids = metrics['user_id'].unique()
        for _ in range(n_iter):
            a_user_ids, b_user_ids = np.random.choice(user_ids, (2, sample_size), False)
            a_metric_values = metrics.loc[metrics['user_id'].isin(a_user_ids), 'metric'].values
            b_metric_values = metrics.loc[metrics['user_id'].isin(b_user_ids), 'metric'].values
            yield a_metric_values, b_metric_values

    def _estimate_errors(self, group_generator, design, effect_add_type):
        pvalues_aa = []
        pvalues_ab = []        
        for a, b in group_generator:
            pvalues_aa.append(self.get_pvalue(a, b, design))            
            if effect_add_type == 'all_const':
                const = b.mean() * design.effect / 100
                b += const                
            elif effect_add_type == 'all_percent':
                b *= (1 + design.effect / 100)                
            else:
                raise ValueError('Неверный тип эффекта')                
            pvalues_ab.append(self.get_pvalue(a, b, design))            
        first_type_error = (np.array(pvalues_aa) < design.alpha).mean()
        second_type_error = (np.array(pvalues_ab) >= design.alpha).mean()        
        return pvalues_aa, pvalues_ab, first_type_error, second_type_error

    def estimate_errors(self, metrics, design, effect_add_type, n_iter):
        group_generator = self._create_group_generator(metrics, design.sample_size, n_iter)
        return self._estimate_errors(group_generator, design, effect_add_type)    
    
    def _generate_bootstrap_metrics(self, data_one, data_two, design):
        bootstrap_data_one = np.random.choice(data_one, (len(data_one), design.bootstrap_iter))
        bootstrap_data_two = np.random.choice(data_two, (len(data_two), design.bootstrap_iter))
        if design.bootstrap_agg_func == 'mean':
            bootstrap_metrics = bootstrap_data_two.mean(axis=0) - bootstrap_data_one.mean(axis=0)
            pe_metric = data_two.mean() - data_one.mean()
            return bootstrap_metrics, pe_metric
        elif design.bootstrap_agg_func == 'quantile 95':
            bootstrap_metrics = (
                np.quantile(bootstrap_data_two, 0.95, axis=0)
                - np.quantile(bootstrap_data_one, 0.95, axis=0)
            )
            pe_metric = np.quantile(data_two, 0.95) - np.quantile(data_one, 0.95)
            return bootstrap_metrics, pe_metric
        else:
            raise ValueError('Неверное значение design.bootstrap_agg_func')

    def _run_bootstrap(self, bootstrap_metrics, pe_metric, design):
        if design.bootstrap_ci_type == 'normal':
            c = stats.norm.ppf(1 - design.alpha / 2)
            se = np.std(bootstrap_metrics)
            ci = (pe_metric - c * se, pe_metric + c * se)        
        elif  design.bootstrap_ci_type == 'percentile':
            ci = (np.quantile(boot_metrics, [design.alpha / 2, 1 - design.alpha / 2]))            
        elif  design.bootstrap_ci_type == 'pivotal':
            right, left = 2 * pe_metric - np.quantile(boot_metrics, [alpha / 2, 1 - alpha / 2])
            ci = (left, right)    
        pvalue = int(ci[0] < 0 < ci[1])
        return ci, pvalue
        
    def get_pvalue(self, metrics_strat_a_group, metrics_strat_b_group, design):
        if design.statistical_test == 'ttest':
            if design.stratification == 'off':
                _, pvalue = stats.ttest_ind(metrics_strat_a_group[:, 0], metrics_strat_b_group[:, 0])
                return pvalue
            elif design.stratification == 'on':
                return self._ttest_strat(metrics_strat_a_group, metrics_strat_b_group)
            else:
                raise ValueError('Неверный design.stratification')
        else:
            raise ValueError('Неверный design.statistical_test')
            
    def _ttest_strat(self, metrics_strat_a_group, metrics_strat_b_group):
        df_control = pd.DataFrame(metrics_strat_a_group, columns=['metric', 'strat'])
        df_pilot = pd.DataFrame(metrics_strat_b_group, columns=['metric', 'strat'])        
        weights = pd.concat([df_control, df_pilot])['strat']\
                    .value_counts(normalize=True).to_dict()
        mean_strat_control = self.calculate_stratified_mean(df_control, weights)
        mean_strat_pilot = self.calculate_stratified_mean(df_pilot, weights)
        var_strat_control = self.calculate_strat_var(df_control, weights)
        var_strat_pilot = self.calculate_strat_var(df_pilot, weights)
        delta_mean_strat = mean_strat_pilot - mean_strat_control
        std_mean_strat = (var_strat_pilot / len(df_pilot) + var_strat_control 
                          / len(df_control)) ** 0.5
        t = delta_mean_strat / std_mean_strat
        pvalue = (1 - stats.norm.cdf(np.abs(t))) * 2
        return pvalue        