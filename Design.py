from scipy import stats

class Design(BaseModel):
    statistical_test: str
    effect: float
    alpha: float = 0.05
    beta: float = 0.1
    bootstrap_iter: int = 1000
    bootstrap_ci_type: str
    bootstrap_agg_func: str
    metric_name: str
    metric_outlier_lower_bound: float
    metric_outlier_upper_bound: float
    metric_outlier_process_type: str
    stratification: str = 'off'