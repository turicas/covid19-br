import rows

class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"

class PtBrDateField2(rows.fields.DateField):
    INPUT_FORMAT = "%d%m%Y"

class CleanIntegerField(rows.fields.IntegerField):

    @classmethod
    def deserialize(cls, value):
        value = str(value or "").strip().replace("*", "")
        if not value or value == "-":
            return 0
        else:
            return int(value)
