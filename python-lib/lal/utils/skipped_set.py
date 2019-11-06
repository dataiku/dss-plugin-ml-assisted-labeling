class MultiuserSet(object):

    def __init__(self, multiuser=False) -> None:
        self.multiuser = multiuser
        if multiuser:
            self.mu_dict = dict()
        else:
            self.mu_set = set()

    def has(self, v, for_user=None):
        if self.multiuser:
            user_set = self.mu_dict.get(for_user)
            return user_set and v in user_set
        else:
            return v in self.mu_set

    def add(self, v, for_user=None):
        if self.multiuser:
            if for_user in self.mu_dict:
                self.mu_dict.get(for_user).add(v)
            else:
                self.mu_dict[for_user] = set(v)
        else:
            self.mu_set.add(v)

    def remove(self, v, for_user=None):
        if self.multiuser:
            if for_user in self.mu_dict:
                self.mu_dict.get(for_user).remove(v)
        else:
            self.mu_set.remove(v)

    def items(self, for_user=None):
        if self.multiuser:
            return self.mu_dict.setdefault(for_user, set())
        else:
            return self.mu_set
