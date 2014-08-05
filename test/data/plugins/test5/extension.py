def preprocess_commands(ctx):
    return (('echo', '"Test5"'),)

def service_commands(ctx):
    return {'server': ('sleep', '5')}

def service_environment(ctx):
    return {'TEST_ENV': ['9876', '5']}

def compile(installer):
    return 0

def configure(ctx):
    ctx['ADDED_BY_EXTENSION'] = True
