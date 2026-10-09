class Drag:
    """
    Encodes a drag coefficient and computes the drag force opposing
    a body's velocity, following the standard quadratic drag
    equation: force magnitude scales with the square of speed and
    always opposes the direction of travel.
    """

    def __init__(self, coefficient):
        """
        Parameters
        ----------
        coefficient : int
            Drag coefficient. Must be a positive integer.
        """
        if not isinstance(coefficient, int) or isinstance(coefficient, bool):
            raise TypeError("Drag coefficient must be a positive integer")

        if coefficient <= 0:
            raise ValueError("Drag coefficient must be a positive integer")

        self.coefficient = coefficient

    def get_force(self, velocity):
        """
        Return the drag force opposing the given velocity vector.

        Parameters
        ----------
        velocity : pymunk.Vec2d
            Current velocity of the body.

        Returns
        -------
        pymunk.Vec2d
            Drag force vector, opposing velocity, with magnitude
            proportional to the square of speed.
        """
        speed = velocity.length

        return velocity * (-self.coefficient * speed)
