##
# Copyright (c) 2013 Sprymix Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import postgresql.exceptions


from metamagic.caos import error as caos_error

from metamagic.exceptions import MetamagicError, _replace_context
from metamagic.utils import markup
from metamagic.utils.lang import context as lang_context


class BackendError(caos_error.CaosError):
    pass


class QueryExceptionContext(markup.MarkupExceptionContext):
    title = 'SQL Query Context'

    def __init__(self, query, position=None):
        super().__init__()
        self.query = query
        self.position = position

    @classmethod
    def as_markup(cls, self, *, ctx):
        me = markup.elements

        if self.position:
            lineno, colno = lang_context.line_col_from_char_offset(self.query, self.position)
        else:
            lineno = colno = None

        tbp = me.lang.TracebackPoint(name='SQL query', filename='<string>',
                                     lineno=lineno, colno=colno)
        tbp.load_source(window=5, lines=self.query.split('\n'))

        src = markup.serializer.serialize_code(self.query, lexer='sql')

        tb_section = me.doc.Section(title='Error Point', body=[tbp])
        src_section = me.doc.Section(title='Full Source', body=[src], collapsed=True)

        return me.lang.ExceptionContext(title=self.title, body=[tb_section, src_section])


class QueryError(BackendError):
    def __init__(self, driver_err, query_text, query_offset=0):
        super().__init__(driver_err.message)
        err_details = getattr(driver_err, 'details', None)
        try:
            position = err_details['position']
        except KeyError:
            position = None
        else:
            try:
                position = int(position) - 1
            except ValueError:
                position = None
            else:
                position -= query_offset

        ctx = QueryExceptionContext(query=query_text, position=position)
        _replace_context(self, ctx)
