from Allocator.models.myuser import MyUser
from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=100)
    users = models.ManyToManyField(MyUser, blank=True, related_name='roles')

    def __str__(self):
        return self.role_name

    @staticmethod
    def get_all_permissions(user):
        roles = user.roles.all()
        all_actions = {}

        for role in roles:
            for perm in role.permissions.all():
                app_name = perm.app_name
                actions = perm.actions.split(',')

                # If app_name already exists, extend the list of actions
                if app_name in all_actions:
                    all_actions[app_name].extend(actions)
                else:
                    all_actions[app_name] = actions

        for app_name in all_actions:
            all_actions[app_name] = list(set(all_actions[app_name]))

        return all_actions
