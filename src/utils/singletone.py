class PostInitSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(PostInitSingleton, cls).__call__(*args, **kwargs)
        elif hasattr(cls, '__post_init__'):
            cls._instances[cls].__post_init__(*args, **kwargs)
        return cls._instances[cls]