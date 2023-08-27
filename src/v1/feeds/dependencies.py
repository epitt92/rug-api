def process_row(row):
    if row['Data'][6].get('ScalarValue') is None:
        value = row['Data'][7]['ScalarValue']
    else:
        value = row['Data'][6]['ScalarValue']

    return {
        'eventHash': row['Data'][0]['ScalarValue'],
        'address': row['Data'][1]['ScalarValue'],
        'blockchain': row['Data'][2]['ScalarValue'],
        'timestamp': row['Data'][3]['ScalarValue'],
        'measureName': row['Data'][4]['ScalarValue'],
        'time': row['Data'][5]['ScalarValue'],
        'value': value
    }