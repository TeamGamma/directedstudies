from fabric.api import env, roles, hosts

def default_roles(*role_list):
    def selectively_attach(func):
        if not env.roles and not env.hosts:
            return roles(*role_list)(func)
        else:
            if env.hosts:
                func = hosts(*env.hosts)(func)
            if env.roles:
                func = roles(*env.roles)(func)
            return func
    return selectively_attach
