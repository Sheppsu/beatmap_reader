class DifficultyHitObject:
    def __init__(self, hit_obj, last_obj, clock_rate):
        self.base_object = hit_obj
        self.last_object = last_obj
        self.delta_time = (hit_obj.time - last_obj.time) / clock_rate
        self.start_time = hit_obj.time / clock_rate
        self.end_time = (hit_obj.end_time if hasattr(hit_obj, "end_time") else hit_obj.time) / clock_rate
