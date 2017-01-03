# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

def generate_sensu_check(check_name, obj):
    obj['handlers'] = ['default']
    obj['subscribers'] = ['sensu-base']
    obj['tags'] = []
    
    content = {'checks':{check_name: obj}}
    return content