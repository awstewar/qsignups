from qsignups.database import DbManager
from qsignups.database.orm import Weekly, Master, AO
from qsignups.database.orm.views import vwWeeklyEvents
from . import UpdateResponse
import ast
from datetime import date
from sqlalchemy import func

def delete(client, user_id, team_id, logger, input_data) -> UpdateResponse:

    weekly_event = DbManager.get_record(vwWeeklyEvents, input_data)

    # in the future we can use the FK from Weekly
    master_filter = [
        Master.team_id == team_id,
        Master.ao_channel_id == weekly_event.ao_channel_id,
        Master.event_day_of_week == weekly_event.event_day_of_week,
        Master.event_time == weekly_event.event_time,
        Master.event_date >= date.today()
    ]

    # Perform deletions
    try:
        DbManager.delete_records(Master, master_filter)
        DbManager.delete_record(Weekly, weekly_event.id)
        return UpdateResponse(success = True, message=f"I've deleted all future {weekly_event.ao_display_name}s from the schedule for {weekly_event.event_day_of_week}s at {weekly_event.event_time} at {weekly_event.ao_display_name}.")
    except Exception as e:
        logger.error(f"Error deleting: {e}")
        return UpdateResponse(success = False, message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Errors:\n{e}")

def edit(client, user_id, team_id, logger, input_data, input_data2) -> UpdateResponse:
    
    # Gather inputs from form
    ao_display_name = input_data['ao_display_name_select']['ao_display_name_select_action']['selected_option']['value']
    event_day_of_week = input_data['event_day_of_week_select']['event_day_of_week_select_action']['selected_option']['value']
    starting_date = input_data['add_event_datepicker']['add_event_datepicker']['selected_date']
    event_time = input_data['event_start_time_select']['event_start_time_select']['selected_time'].replace(':','')
    event_end_time = input_data['event_end_time_select']['event_end_time_select']['selected_time'].replace(':','')

    og_ao_channel_id, og_event_day_of_week, og_event_time = input_data2.split('|')

    # Logic for custom events
    if input_data['event_type_select']['event_type_select_action']['selected_option']['value'] == 'Custom':
        event_type = input_data['event_type_custom']['event_type_custom']['value']
    else:
        event_type = input_data['event_type_select']['event_type_select_action']['selected_option']['value']

    event_recurring = True

    try:
        # Grab channel id
        ao: AO = DbManager.find_records(AO, [AO.team_id == team_id, AO.ao_display_name == ao_display_name])[0]
        ao_channel_id = ao.ao_channel_id
        
        # Update Weekly table
        DbManager.update_records(cls=Weekly, filters=[
            Weekly.team_id == team_id,
            Weekly.ao_channel_id == og_ao_channel_id,
            Weekly.event_day_of_week == og_event_day_of_week,
            Weekly.event_time == og_event_time
        ], fields={
            Weekly.ao_channel_id: ao_channel_id,
            Weekly.event_day_of_week: event_day_of_week,
            Weekly.event_time: event_time,
            Weekly.event_end_time: event_end_time,
            Weekly.event_type: event_type,
            Weekly.team_id: team_id
        })

        # Support for changing day of week
        if event_day_of_week != og_event_day_of_week:
            day_list = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            new_dow_num = day_list.index(event_day_of_week)
            old_dow_num = day_list.index(og_event_day_of_week)
            day_adjust = new_dow_num - old_dow_num
        else:
            day_adjust = 0
            
        # Update Master table
        DbManager.update_records(cls=Master, filters=[
            Master.team_id == team_id,
            Master.ao_channel_id == og_ao_channel_id,
            Master.event_day_of_week == og_event_day_of_week,
            Master.event_time == og_event_time,
            Master.event_date >= starting_date
        ], fields={
            Master.ao_channel_id: ao_channel_id,
            Master.event_date: func.ADDDATE(Master.event_date, day_adjust),
            Master.event_day_of_week: event_day_of_week,
            Master.event_time: event_time,
            Master.event_end_time: event_end_time,
            Master.event_type: event_type,
            Master.team_id: team_id,
            Master.event_recurring: event_recurring
        })

        return UpdateResponse(success = True, message=f"Got it - I've made your updates!")
    except Exception as e:
        logger.error(f"Error updating: {e}")
        return UpdateResponse(success = False, message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Errors:\n{e}")

