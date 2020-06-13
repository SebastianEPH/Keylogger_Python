import mi
import wmi

# This sample describes the usage of custom operation options
# by creating a nic team.

conn = wmi.WMI(moniker='root/standardcimv2')

def new_lbfo_team(team_members, team_name):
    obj = conn.MSFT_NetLbfoTeam.new()
    obj.Name = 'nic_team'
    custom_options = [
        {'name': 'TeamMembers',
         'value_type': mi.MI_ARRAY | mi.MI_STRING,
         'value': team_members
        },
        {'name': 'TeamNicName',
         'value_type': mi.MI_STRING,
         'value': 'nic_team'}
    ]
    operation_options = {'custom_options': custom_options}
    obj.put(operation_options=operation_options)

new_lbfo_team(team_members=['eth2', 'eth3'],
              team_name='nic_team')
