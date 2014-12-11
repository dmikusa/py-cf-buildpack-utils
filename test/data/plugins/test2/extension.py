def preprocess_commands(ctx):
    return (('echo', '"Wheee"'),)


def service_commands(ctx):
    return {'server': ('sleep', '2')}


def service_environment(ctx):
    return {'TEST_ENV': '4321'}


def compile(installer):
    print 'Fail :('
    return -1
