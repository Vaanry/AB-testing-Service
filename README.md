# AB-testing-Service
Set of tools for A/B-testing.
Сервис для осуществление полного пайплайна A/B-тестирования.

DataService
Класс, предоставляющий доступ к сырым данным.
        
        :param table_name_2_table (dict[str, pd.DataFrame]): словарь таблиц с данными.
            Пример, {
                'sales': pd.DataFrame({'sale_id': ['123', ...], ...}),
                ...
            }. 

get_data_subset
        Возвращает подмножество данных.

        :param table_name (str): название таблицы с данными.
        :param begin_date (datetime.datetime): дата начала интервала с данными.
            Пример, df[df['date'] >= begin_date].
            Если None, то фильтровать не нужно.
        :param end_date (None, datetime.datetime): дата окончания интервала с данными.
            Пример, df[df['date'] < end_date].
            Если None, то фильтровать не нужно.
        :param user_ids (None, list[str]): список user_id, по которым нужно предоставить данные.
            Пример, df[df['user_id'].isin(user_ids)].
            Если None, то фильтровать по user_id не нужно.
        :param columns (None, list[str]): список названий столбцов, по которым нужно предоставить данные.
            Пример, df[columns].
            Если None, то фильтровать по columns не нужно.
        :return df (pd.DataFrame): датафрейм с подмножеством данных.

Design
Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала. ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']


MetricsService
Класс для вычисления метрик.
        :param data_service (DataService): объект класса, предоставляющий доступ к данным.
        

_get_data_subset(self, table_name, begin_date, end_date, user_ids=None, columns=None):
        Возвращает часть таблицы с данными.


_calculate_response_time
        Вычисляет значения времени обработки запроса сервером.
        
        Нужно вернуть значения user_id и load_time из таблицы 'web-logs', отфильтрованные по date и user_id.
        Считаем, что каждый запрос независим, поэтому группировать по user_id не нужно.

        :param begin_date, end_date (datetime): период времени, за который нужно считать значения.
        :param user_id (None, list[str]): id пользователей, по которым нужно отфильтровать полученные значения.
        
        :return (pd.DataFrame): датафрейм с двумя столбцами ['user_id', 'metric']



_calculate_revenue_web
        Вычисляет значения выручки с пользователя за указанный период для заходивших на сайт в указанный период.

        Эти данные нужны для экспериментов на сайте, когда в эксперимент попадают только те, кто заходил на сайт.

        :param begin_date, end_date (datetime): период времени, за который нужно считать значения.
        :param user_id (None, list[str]): id пользователей, по которым нужно отфильтровать полученные значения.
        
        :return (pd.DataFrame): датафрейм с двумя столбцами ['user_id', 'metric']


_calculate_revenue_all
        Вычисляет значения выручки с пользователя за указанный периодтдля заходивших на сайт до end_date.

        Эти данные нужны, например, для экспериментов с рассылкой по email, когда в эксперимент попадают те, кто когда-либо оставил нам свои данные.
     
        :param begin_date, end_date (datetime): период времени, за который нужно считать значения.
        :param user_id (None, list[str]): id пользователей, по которым нужно отфильтровать полученные значения.
        
        :return (pd.DataFrame): датафрейм с двумя столбцами ['user_id', 'metric']


calculate_metric
        Считает значения метрики.

        :param metric_name (str): название метрики
        :param begin_date (datetime): дата начала периода (включая границу)
        :param end_date (datetime): дата окончания периода (не включая границу)
        :param cuped (str): применение CUPED. ['off', 'on (previous week revenue)']
            'off' - не применять CUPED
            'on (previous week revenue)' - применяем CUPED, в качестве ковариаты
                используем выручку за прошлые 7 дней
        :param user_ids (list[str], None): список пользователей.
            Если None, то вычисляет метрику для всех пользователей.
        :return df: columns=['user_id', 'metric']

process_outliers
        Возвращает новый датафрейм с обработанными выбросами в измерениях метрики.

        :param metrics (pd.DataFrame): таблица со значениями метрики, columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :return df: columns=['user_id', 'metric']

calculate_linearized_metrics
        Считает значения метрики отношения.
        Нужно вычислить параметр kappa (коэффициент в функции линеаризации) по данным из
        control_metrics и использовать его для вычисления линеаризованной метрики.

        :param control_metrics (pd.DataFrame): датафрейм со значениями метрики контрольной группы.
            Значения в столбце 'user_id' не уникальны.
            Измерения для одного user_id считаем зависимыми, а разных user_id - независимыми.
            columns=['user_id', 'metric']
        :param pilot_metrics (pd.DataFrame): датафрейм со значениями метрики экспериментальной группы.
            Значения в столбце 'user_id' не уникальны.
            Измерения для одного user_id считаем зависимыми, а разных user_id - независимыми.
            columns=['user_id', 'metric']
        :param control_user_ids (list): список id пользователей контрольной группы, для которых
            нужно рассчитать метрику. Если None, то использовать пользователей из control_metrics.
            Если для какого-то пользователя нет записей в таблице control_metrics, то его
            линеаризованная метрика равна нулю.
        :param pilot_user_ids (list): список id пользователей экспериментальной группы, для которых
            нужно рассчитать метрику. Если None, то использовать пользователей из pilot_metrics.
            Если для какого-то пользователя нет записей в таблице pilot_metrics, то его
            линеаризованная метрика равна нулю.
        :return lin_control_metrics, lin_pilot_metrics: columns=['user_id', 'metric']


 Design
 Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала. ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']
    metric_name - название целевой метрики эксперимента
    metric_outlier_lower_bound - нижняя допустимая граница метрики, всё что ниже считаем выбросами
    metric_outlier_upper_bound - верхняя допустимая граница метрики, всё что выше считаем выбросами
    metric_outlier_process_type - способ обработки выбросов. ['drop', 'clip'].
        'drop' - удаляем измерение, 'clip' - заменяем выброс на значение ближайшей границы (lower_bound, upper_bound).
    stratification - постстратификация. 'on' - использовать постстратификация, 'off - не использовать.


ExperimentsService
Класс для проведения статистических тестов.
get_pvalue
        Применяет статтест, возвращает pvalue.

        :param metrics_a_group (np.array): массив значений метрик группы A
        :param metrics_a_group (np.array): массив значений метрик группы B
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value
        
estimate_sample_size
        Оцениваем необходимый размер выборки для проверки гипотезы о равенстве средних.
        
        :param metrics (pd.DataFrame): датафрейм со значениями метрик из MetricsService.
            columns=['user_id', 'metric']
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (int): минимально необходимый размер групп (количество пользователей)
        """


_create_group_generator
        Генератор случайных групп.

        :param metrics (pd.DataFame): таблица с метриками, columns=['user_id', 'metric'].
        :param sample_size (int): размер групп (количество пользователей в группе).
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return (np.array, np.array): два массива со значениями метрик в группах.

_estimate_errors
        Оцениваем вероятности ошибок I и II рода.

        :param group_generator: генератор значений метрик для двух групп.
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B в (1 + effect / 100) раз.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]), first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей ошибок I и II рода.


estimate_errors
        Оцениваем вероятности ошибок I и II рода.

        :param metrics (pd.DataFame): таблица с метриками, columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B в (1 + effect / 100) раз.
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]), first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей ошибок I и II рода.


_generate_bootstrap_metrics
        Генерирует значения метрики, полученные с помощью бутстрепа.
        
        :param data_one, data_two (np.array): значения метрик в группах.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return bootstrap_metrics, pe_metric:
            bootstrap_metrics (np.array) - значения статистики теста псчитанное по бутстрепным подвыборкам
            pe_metric (float) - значение статистики теста посчитанное по исходным данным


_run_bootstrap
        Строит доверительный интервал и проверяет значимость отличий с помощью бутстрепа.
        
        :param bootstrap_metrics (np.array): статистика теста, посчитанная на бутстрепных выборках.
        :param pe_metric (float): значение статистики теста посчитанное по исходным данным.
        :return ci, pvalue:
            ci [float, float] - границы доверительного интервала
            pvalue (float) - 0 если есть статистически значимые отличия, иначе 1.


get_pvalue(self, metrics_a_group, metrics_b_group, design):
        Применяет статтест, возвращает pvalue.

        :param metrics_strat_a_group (np.ndarray): значения метрик и страт группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и страт группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value


_ttest_strat
        Применяет постстратификацию, возвращает pvalue.

        Веса страт считаем по данным обеих групп.
        Предполагаем, что эксперимент проводится на всей популяции.
        Веса страт нужно считать по данным всей популяции.

        :param metrics_strat_a_group (np.ndarray): значения метрик и страт группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и страт группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value


Experiment
    id - идентификатор эксперимента.
    buckets_count - необходимое количество бакетов.
    conflicts - список идентификаторов экспериментов, которые нельзя проводить
        одновременно на одних и тех же пользователях.


SplittingService
Класс для распределения экспериментов и пользователей по бакетам.

        :param buckets_count (int): количество бакетов.
        :param bucket_salt (str): соль для разбиения пользователей по бакетам.
            При одной соли каждый пользователь должен всегда попадать в один и тот же бакет.
            Если изменить соль, то распределение людей по бакетам должно измениться.
        :param buckets (list[list[int]]) - список бакетов, в каждом бакете перечислены идентификаторы
            эксперименты, которые в нём проводятся.
        :param id2experiment (dict[int, Experiment]) - словарь пар: идентификатор эксперимента - эксперимент.

add_experiment
        Проверяет можно ли добавить эксперимент, добавляет если можно.

        :param experiment (Experiment): параметры эксперимента, который нужно запустить
        :return success, buckets:
            success (boolean) - можно ли добавить эксперимент, True - можно, иначе - False
            buckets (list[list[int]]]) - список бакетов, в каждом бакете перечислены идентификаторы экспериментов,
                которые в нём проводятся.


process_user
Определяет в какие эксперименты попадает пользователь.

        Сначала нужно определить бакет пользователя.
        Затем для каждого эксперимента в этом бакете выбрать пилотную или контрольную группу.

        :param user_id (str): идентификатор пользователя
        :return bucket_id, experiment_groups:
            - bucket_id (int) - номер бакета (индекс элемента в self.buckets)
            - experiment_groups (list[tuple]) - список пар: id эксперимента, группа.
                Группы: 'A', 'B'.
            Пример: (8, [(194, 'A'), (73, 'B')])


get_bucket
        Определяет бакет по id.

        value - уникальный идентификатор объекта.
        n - количество бакетов.
        salt - соль для перемешивания.