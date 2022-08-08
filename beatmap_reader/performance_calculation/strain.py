import math


class ReverseQueue:
    def __init__(self, initial_capacity):
        self.items = [None for _ in range(initial_capacity)]
        self.capacity = initial_capacity
        self.start = 0
        self.count = 0

    def __getitem__(self, index):
        reverse_index = self.count - 1 - index
        return self.items[(self.start + reverse_index) % self.capacity]

    def enqueue(self, item):
        if self.count == self.capacity:
            buffer = [None for _ in range(self.capacity * 2)]

            for i in range(self.count):
                buffer[i] = self.items[(self.start + i) % self.capacity]

            self.items = buffer
            self.capacity *= 2
            self.start = 0

        self.items[(self.start + self.count) % self.capacity] = item
        self.count += 1

    def dequeue(self):
        item = self.items[self.start]
        self.start = (self.start + 1) % self.capacity
        self.count -= 1
        return item

    def clear(self):
        self.start = 0
        self.count = 0

    def __len__(self):
        return self.count


class Skill:
    history_length = 1

    def __init__(self, mods):
        self.mods = mods
        self.previous = ReverseQueue(self.history_length + 1)

    def process_internal(self, hit_object):
        while len(self.previous) > self.history_length:
            self.previous.dequeue()

        self.process(hit_object)
        self.previous.enqueue(hit_object)

    def process(self, hit_object):
        raise NotImplementedError()

    def difficulty_value(self):
        raise NotImplementedError()


class StrainSkill(Skill):
    decay_weight = 0.9
    section_length = 400

    def __init__(self, mods):
        super().__init__(mods)
        self.current_section_peak = 0
        self.current_section_end = 0
        self.strain_peaks = []

    def strain_value_at(self, hit_object):
        raise NotImplementedError()

    def process(self, hit_object):
        if len(self.previous) == 0:
            self.current_section_end = math.ceil(hit_object.start_time / self.section_length) * self.section_length

        while hit_object.start_time > self.current_section_end:
            self.save_current_peak()
            self.start_new_section_from(self.current_section_end)
            self.current_section_end += self.section_length

        self.current_section_peak = max(self.strain_value_at(hit_object), self.current_section_peak)

    def save_current_peak(self):
        self.strain_peaks.append(self.current_section_peak)

    def start_new_section_from(self, start_time):
        self.current_section_peak = self.calculate_initial_strain(start_time)

    def calculate_initial_strain(self, start_time):
        raise NotImplementedError()

    def get_current_strain_peaks(self):
        return self.strain_peaks + [self.current_section_peak]

    def difficulty_value(self):
        difficulty = 0.0
        weight = 1.0

        for strain in sorted(self.get_current_strain_peaks(), reverse=True):
            difficulty += strain * weight
            weight *= self.decay_weight

        return difficulty
    

class StrainDecaySkill(StrainSkill):
    def __init__(self, mods):
        super().__init__(mods)
        self.skill_multiplier = 0
        self.strain_decay_base = 0
        self.current_strain = 0

    def calculate_initial_strain(self, start_time):
        return self.current_strain * self.strain_decay(start_time - self.previous[0].start_time)

    def strain_value_at(self, hit_object):
        self.current_strain *= self.strain_decay(hit_object.delta_time)
        self.current_strain += self.strain_value_of(hit_object) * self.skill_multiplier

        return self.current_strain

    def strain_value_of(self, hit_object):
        raise NotImplementedError()

    def strain_decay(self, ms):
        return math.pow(self.strain_decay_base, ms / 1000)
