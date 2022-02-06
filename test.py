from arknights_cards import *

tokens = ['tokne1', 'token2'] # TODO Token
for token in tokens:
    ak_cards = arknights_cards(token, 'ak_server.db') # TODO 数据库名称需要统一
    ak_cards.show() # 显示当前用户数据
    ak_cards.update_cards_db() # 将获取到的寻访记录增量更新到数据库中

    ak_cards.get_cards_number() # 获取抽卡详细数据，即总计抽数，以及每个星级的抽数
    ak_cards.get_cards_number_pool() # 获取各卡池抽卡次数
    ak_cards.get_cards_pool_guarantee_count() # 获取各卡池保底状况，即已累计多少抽未出六星
    ak_cards.get_cards_six_history() # 获取抽到的六星历史记录
    ak_cards.get_cards_count_avg() # 获取各卡池平均出货抽数