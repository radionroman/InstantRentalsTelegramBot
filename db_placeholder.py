from src.utils.constants import DEFAULT_USER_DATA
from collections import defaultdict


def init():
    global user_data 
    user_data = defaultdict(lambda: DEFAULT_USER_DATA.copy())