from math import ceil
from flask import Markup, request, url_for

NAV = "<nav>\n  <ul class='pagination justify-content-center'>\n{}  </ul>\n</nav>\n"
PREVIOUS = "    <li class='page-item'><a class='page-link' href='{}'>Previous</a></li>\n"
PREVIOUS_DISABLED = "    <li class='page-item disabled'><a class='page-link'>Previous</a></li>\n"
NEXT = "    <li class='page-item'><a class='page-link' href='{}'>Next</a></li>\n"
NEXT_DISABLED = "    <li class='page-item disabled'><a class='page-link'>Next</a></li>\n"
PAGE = "    <li class='page-item'><a class='page-link' href='{}'>{}</a></li>\n"
CURRENT_PAGE = "    <li class='page-item active'><span class='page-link'>{}</span></li>\n"
GAP = "    <li class='page-item disabled'><span class='page-link'>...</span></li>\n"
INFO = "<a class='text-secondary'>Total: {}</a>"


class Pagination:
    def __init__(self, **kwargs):
        self.per_page = kwargs.get('per_page', 10)
        self.page = kwargs.get('page', 1)
        self.record = kwargs.get('record', 0)
        self.total = ceil(self.record/self.per_page)
        args = request.args.copy()
        self.args = {}
        for key, value in args.lists():
            if len(value) == 1:
                self.args[key] = value[0]
            else:
                self.args[key] = value
        self.has_prev = self.page > 1
        self.has_next = self.page < self.total

    def href(self, page):
        self.args['page'] = page
        return url_for(request.endpoint, **self.args)

    @property
    def prev_page(self):
        if self.has_prev:
            page = self.page - 1 if self.page > 2 else 1
            url = self.href(page)
            return PREVIOUS.format(url)
        return PREVIOUS_DISABLED

    @property
    def pages(self):
        structure = sorted(list(
            set([1, 2, self.total-1, self.total]+list(range(self.page-2, self.page+3)))))
        pages = ''
        flag = 0
        for i in structure:
            if i >=1 and i <= self.total:
                if i-flag != 1:
                    pages += GAP
                if i == self.page:
                    pages += CURRENT_PAGE.format(i)
                else:
                    pages += PAGE.format(self.href(i), i)
                flag = i
        return pages

    @property
    def next_page(self):
        if self.has_next:
            return NEXT.format(self.href(self.page + 1))
        return NEXT_DISABLED

    @property
    def nav(self):
        '''Get all the pagination nav.'''
        if self.total <= 1:
            return ''
        return Markup(NAV.format(self.prev_page+self.pages+self.next_page))

    @property
    def info(self):
        '''Get the pagination info.'''
        return Markup(INFO.format(self.record))
