from netbox_onboarding.netbox_keeper import NetboxKeeper


class Onboarding(object):
    def __init__(self):
        self.created_device = None


class StandaloneOnboarding(Onboarding):
    def run(self, onboarding_kwargs):
        nb = NetboxKeeper(**onboarding_kwargs)
        nb.ensure_device()

        self.created_device = nb.device
