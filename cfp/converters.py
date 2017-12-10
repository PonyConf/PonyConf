class SignedIntConverter:
    regex = '[+-]?[0-9]+'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%+d' % value
