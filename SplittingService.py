from pydantic import BaseModel
from copy import copy
from hashlib import md5

class Experiment(BaseModel):
    id: int
    buckets_count: int
    conflicts: list[int] = []

class SplittingService:
    def __init__(self, buckets_count, bucket_salt, buckets=None, id2experiment=None):
        self.buckets_count = buckets_count
        self.bucket_salt = bucket_salt
        if buckets:
            self.buckets = buckets
        else:
            self.buckets = [[] for _ in range(buckets_count)]
        if id2experiment:
            self.id2experiment = id2experiment
        else:
            self.id2experiment = {}

    def add_experiment(self, experiment):
        if self.buckets_count < experiment.buckets_count:
            return False, self.buckets
        
        conflicts = set(experiment.conflicts)
        test_buckets = copy(self.buckets)        
        for _ in range(experiment.buckets_count):
            for bucket in test_buckets:
                if conflicts.intersection(set(bucket)) == set() and experiment.id not in bucket:
                    bucket.append(experiment.id)
                    break
                else:
                    continue                    
        if sum(map(lambda x: experiment.id in x, self.buckets)) == experiment.buckets_count:
            self.buckets = test_buckets
            return True, self.buckets
        return False, self.buckets
    
    def process_user(self, user_id):
        bucket_id = self.get_bucket(user_id, self.buckets_count, self.bucket_salt)        
        experiment_groups = []
        if self.id2experiment:
            for exp_id, exp in self.id2experiment.items():
                if exp_id in self.buckets[bucket_id]:
                    n_group = self.get_bucket(user_id, 2, exp.salt)
                    group = 'B' if n_group == 1 else 'A'
                    experiment_groups.append((exp_id, group))            
        return bucket_id, experiment_groups
            
    @staticmethod        
    def get_bucket(value: str, n: int, salt: str=''):
        hash_value = int(md5((value + salt).encode()).hexdigest(), 16)
        return hash_value % n
            