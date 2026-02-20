import random
from scraper.settings import USER_AGENT_LIST


class RandomUserAgentMiddleware:
    def __init__(self):
        self.user_agents = USER_AGENT_LIST

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.user_agents)
