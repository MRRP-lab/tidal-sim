from variable import VelocityEffect


class VectorField():
    def __init__(self, sim_state):
        self.sim_state = sim_state
        self._forces = []

    def add(self, force):
        if not isinstance(force, VelocityEffect):
            raise TypeError("force must implement VelocityEffect")
        self._forces.append(force)

    def get(self, index):
        return self._forces[index]

    def removeAtIndex(self, index):
        return self._forces.pop(index)

    # matches pymunk's required Body.velocity_func(body, gravity, damping, dt) signature
    def __call__(self, body, gravity, damping, dt):
        t = self.sim_state["time"]
        velocity = body.velocity
        for effect in self._forces:
            velocity = effect.apply(t, velocity, body)
        body.velocity = velocity
