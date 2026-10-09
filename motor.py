class Motor:
    # turns throttle and steering commands into forces on the boat's body
    #   throttle, -1..1: + pushes forward along the hull (up to forward_force);
    #     - pushes the opposite way the boat points (up to reverse_force)
    #   steering, -1..1: pushes the stern sideways (up to steering_force),
    #     which turns the boat; + turns it clockwise, to starboard
    # stern_offset: how far behind the body's center the steering force acts, pixels
    def __init__(self, forward_force, reverse_force, steering_force, stern_offset):
        self.forward_force = forward_force
        self.reverse_force = reverse_force
        self.steering_force = steering_force
        self.stern_offset = stern_offset

    # applies one step's forces; returns the commands after clamping to -1..1.
    # pymunk clears the forces after each step, so this is called every step
    def apply(self, body, throttle, steering):
        throttle = min(max(throttle, -1.0), 1.0)
        steering = min(max(steering, -1.0), 1.0)
        thrust = throttle*(self.forward_force if throttle > 0 else self.reverse_force)
        # body-local axes: x points out the bow, y to starboard
        body.apply_force_at_local_point((thrust, 0))
        # pushing the stern to port swings the bow to starboard
        body.apply_force_at_local_point((0, -steering*self.steering_force), (-self.stern_offset, 0))
        return throttle, steering
