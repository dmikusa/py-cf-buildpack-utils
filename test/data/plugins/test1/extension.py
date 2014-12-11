def preprocess_commands(ctx):
    return (('ls', '-l'),)


def service_commands(ctx):
    return {'server': ('sleep', '1')}


def service_environment(ctx):
    return {'TEST_ENV': '1234'}


def compile(installer):
    print 'Hello World!'
    return 0
