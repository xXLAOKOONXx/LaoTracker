import cassiopeia as cass

with open('lao_tracker/RIOT_API_KEY', 'r') as file:
    key = file.read()
    
cass.apply_settings('./static_data/cass_config.json')
cass.set_riot_api_key(key)

