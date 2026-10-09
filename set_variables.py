class SetVariables:
    # writes the Prompter's answers into the loaded config params, in the
    # keys and units configs/global_config.yaml uses, so the rest of
    # run_sim.py runs from them exactly as if they'd been in the file
    def __init__(self, params):
        self.params = params

    def apply(self, answers):
        self.params["sim_time"] = int(round(answers["run_hours"]*3600)) # hours -> seconds
        spawn = answers["spawn"]
        self.params["start"] = None if spawn is None else [spawn[0], spawn[1]]
        waypoint = answers["waypoint"]
        self.params["waypoint"] = None if waypoint is None else [waypoint[0], waypoint[1]]
        self.params["log"] = answers["log"]
        return self.params
