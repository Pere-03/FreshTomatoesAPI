from rest_framework.pagination import PageNumberPagination


class HTTPSPageNumberPagination(PageNumberPagination):
    def get_next_link(self):
        next_link = super().get_next_link()
        if next_link is not None:
            return next_link.replace("http://", "https://")
        return None

    def get_previous_link(self):
        previous_link = super().get_previous_link()
        if previous_link is not None:
            return previous_link.replace("http://", "https://")
        return None
