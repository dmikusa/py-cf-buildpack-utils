def preprocess_commands(ctx):
    return (('echo', '"Test4"'),)

def service_commands(ctx):
    return {'server': ('sleep', '4')}

def service_environment(ctx):
    return {'TEST_ENV': ['9876', '0123-']}

def compile(installer):
    raise ValueError("Intentional")
    return 0

def configure(ctx):
    raise ValueError("Intentional")
