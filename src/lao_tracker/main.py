import pickle
import time
import datetime
import logging
import riotwatcher
import pandas as pd

with open('lao_tracker/RIOT_API_KEY.txt', 'r') as file:
    key = file.read()

lol_api = riotwatcher.LolWatcher(key)

summoner_region = 'euw1'
match_region = 'europe'
thresh_id = 412
data_table_file = 'data/df.file'
lp_data_file = 'data/lp.file'
relic_shield_tier_1_id = 3858
relic_shield_tier_2_id = 3859
relic_shield_tier_2_id = 3860
shoulderguards_tier_1_id = 3854
shoulderguards_tier_2_id = 3855
shoulderguards_tier_3_id = 3857
oracle_lens_id = 3364

# Activate logging File
logging.basicConfig(filename='updater.log', level=logging.DEBUG)

def loop_step():

    rows = []

    old_df = pd.DataFrame()
    # Import existing DF
    try:
        with open(data_table_file, 'rb') as f:
            old_df = pickle.load(f)
            rows.append(old_df)
    except IOError:
        logging.warning('No Data Table File!')


    # Check current game against existance
    sum_name = 'xXLAOKOONXx'
    summoner = lol_api.summoner.by_name(region='euw1', summoner_name=sum_name)

    # Add DF Line to LP Timeline

    league_info = lol_api.league.by_summoner('euw1', summoner['id'])
    
    comulated_lp = 0

    for item in league_info:
        if item['queueType'] == 'RANKED_SOLO_5x5':
            tier = item['tier']
            tier_points = 0
            if tier == 'IRON':
                tier_points = 0
            elif tier == 'BRONCE':
                tier_points = 400
            elif tier == 'SILVER':
                tier_points = 800
            elif tier == 'GOLD':
                tier_points = 1200
            elif tier == 'PLATIN':
                tier_points = 1600

            rank = item['rank']
            rank_points = 0
            if rank == 'IV':
                rank_points = 0
            elif rank == 'III':
                rank_points = 100
            elif rank == 'II':
                rank_points = 200
            elif rank == 'I':
                rank_points = 300

            league_points = item['leaguePoints']

            comulated_lp = tier_points + rank_points + league_points

            logging.info(f'{summoner["name"]} is {tier} {rank} with {league_points} LP which equals a score of {comulated_lp} comulated LP')

    match_list = lol_api.match.matchlist_by_puuid(region='europe', puuid=summoner['puuid'], start=0, count=100, queue=420)

    cur_match = match_list[0]


    lp_rows = []

    time_stemp_now = datetime.datetime.now()

    new_df_line = pd.DataFrame({
        'SummonerName':summoner['name'],
        'Timestemp':datetime.datetime.now(),
        'comulatedLP':comulated_lp,
        'recentGame':cur_match,
    }, index=[time_stemp_now])
    lp_rows.append(new_df_line)

    # Import existing DF
    try:
        with open(lp_data_file, 'rb') as f:
            lp_rows.append(pickle.load(f))
    except IOError:
        logging.warning('No LP File!')

    complete_df = pd.concat(lp_rows)
    
    lp_file_dump = open(lp_data_file,'wb')
    pickle.dump(complete_df, lp_file_dump)
    lp_file_dump.close()

    # if new matches exist do calcs

    logging.debug(f'Most recent match id: {cur_match}')
    if cur_match in old_df.index:
        logging.info('Current match already registered in file')
        return
    logging.debug('Start calculations for match analysis')

    match_id = cur_match

    summoner_puuid = summoner['puuid']
    summoner_name = summoner['name']

    for match_id in match_list:

        if match_id in old_df.index:
            break

        participant_id = -1

        # -----MATCH-----

        match = lol_api.match.by_id(region=match_region, match_id=match_id)

        time_stamp = float(match['info']['gameCreation'])
        time_stamp = datetime.datetime.fromtimestamp(time_stamp / 1e3)

        participants = match['info']['participants']
        first_blood = False
        team_id = 0
        threshPickedByOther = False

        for p in participants:
            if p['puuid'] == summoner_puuid:
                if p['firstBloodKill'] or p['firstBloodAssist']:
                    first_blood = True
                win = p['win']
                kills = p['kills']
                deaths = p['deaths']
                assists = p['assists']
                team_id = p['teamId']
                support = p['teamPosition'] == 'UTILITY'
                threshPicked = p['championId'] == thresh_id
                participant_id = p['participantId']
            if p['puuid'] != summoner_puuid:
                if p['championId'] is thresh_id:
                    threshPickedByOther = True

        threshBan = False

        teams = match['info']['teams']
        for t in teams:
            if t['teamId'] is team_id:
                team_dragons = t['objectives']['dragon']['kills']
                first_dragon = t['objectives']['dragon']['first']
                for b in t['bans']:
                    if b['championId'] == thresh_id:
                        threshBan = True

            if t['teamId'] is not team_id:
                enemy_dragons = t['objectives']['dragon']['kills']
                for b in t['bans']:
                    if b['championId'] == thresh_id:
                        threshBan = True

        gametime = match['info']['gameDuration']
        gametime = datetime.timedelta(seconds=gametime)

        
        # ----MATCHTIMELINE----

        match_timeline = lol_api.match.timeline_by_match(region=match_region, match_id=match_id)

        tier_2_upgrade = gametime
        red_trinket_switch = gametime
        tier_3_upgrade = gametime

        frames = match_timeline['info']['frames']
        for f in frames:
            for e in f['events']:
                if e['type'] == 'ITEM_DESTROYED' and e['participantId'] == participant_id:
                    if e['itemId'] == relic_shield_tier_1_id or e['itemId'] == shoulderguards_tier_1_id:
                        tier_2_upgrade = datetime.timedelta(milliseconds=e['timestamp'])
                    if e['itemId'] == relic_shield_tier_2_id or e['itemId'] == shoulderguards_tier_2_id:
                        tier_3_upgrade = datetime.timedelta(milliseconds=e['timestamp'])
                elif e['type'] == 'ITEM_PURCHASED' and e['participantId'] == participant_id:
                    if e['itemId'] == oracle_lens_id:
                        red_trinket_switch = datetime.timedelta(milliseconds=e['timestamp'])



        # ----DICT----

        d = {
            'Name':summoner_name, 
            'id':match_id, 
            'timestamp':time_stamp,
            'firstbloodParticipation':first_blood,
            'gametime': gametime,
            'win': win,
            'kills':kills,
            'assists':assists,
            'deaths':deaths,
            'teamDragons':team_dragons,
            'enemyDragons':enemy_dragons,
            'firstDragon':first_dragon,
            'support':support,
            'threshBan':threshBan,
            'threshPickedByOther':threshPickedByOther,
            'threshPicked':threshPicked,
            'redTrinketPurchase':red_trinket_switch,
            'tier2Upgrade':tier_2_upgrade,
            'tier3Upgrade':tier_3_upgrade,
            }

        df = pd.DataFrame(d, index=[match_id])
        rows.append(df)

    complete_df = pd.concat(rows)

    df_file_dump = open(data_table_file,'wb')
    pickle.dump(complete_df, df_file_dump)
    df_file_dump.close()
    
    return

def main_loop():
    sleep_duration = 1800
    error_sleep_duration = 600
    logging.info(f'Main Loop started with sleep time of {sleep_duration} seconds')

    while(True):
        try:
            logging.debug('Start next step')
            loop_step()
            logging.debug(f'Step finished, sleeping for {sleep_duration}')
            time.sleep(sleep_duration)
        except riotwatcher.ApiError as ex:
            logging.critical(f'Api Error: {str(ex)}')
            time.sleep(error_sleep_duration)
        except Exception as ex:
            logging.critical(f'Unhandled Error: {str(ex)}')
            time.sleep(error_sleep_duration)


    return

main_loop()
