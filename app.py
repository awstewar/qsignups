import logging
import os
from datetime import datetime, timedelta, date
import pandas as pd

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.adapter.aws_lambda.lambda_s3_oauth_flow import LambdaS3OAuthFlow

from qsignups.utilities import safe_get, get_user_name
from qsignups.database import my_connect

from qsignups.slack import forms
from qsignups.slack.forms import ao, event, home, settings
from qsignups.slack.handlers import settings as settings_handler, weekly as weekly_handler
from qsignups.slack import actions, inputs

def get_oauth_flow():
    if os.environ.get("SLACK_BOT_TOKEN"):
        return None
    else:
        return LambdaS3OAuthFlow()

# process_before_response must be True when running on FaaS
app = App(
  process_before_response=True,
  oauth_flow=get_oauth_flow(),
)

# Inputs
schedule_create_length_days = 365

@app.action(actions.REFRESH_ACTION)
def handle_refresh_home_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    user_name = get_user_name([user_id], logger, client)
    top_message = f'Welcome to QSignups, {user_name}!'
    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    logger.info(f'INFO: {body}')
    say("Looking for me? Click on my icon to go to the app and sign up to Q!")

@app.command("/hello")
def respond_to_slack_within_3_seconds(ack):
    # This method is for synchronous communication with the Slack API server
    ack("Thanks!")

@app.command("/schedule")
def display_upcoming_schedule(ack):
    # This method is for synchronous communication with the Slack API server
    ack("To be implemented: Upcoming Schedule!")

@app.event("app_home_opened")
def update_home_tab(client, event, logger, context):
    logger.info(event)
    user_id = context["user_id"]
    team_id = context["team_id"]
    user_name = get_user_name([user_id], logger, client)
    top_message = f'Welcome to QSignups, {user_name}!'
    home.refresh(client, user_id, logger, top_message, team_id, context)


# triggers when user chooses to schedule a q
# @app.action("schedule_q_button")
# def handle_take_q_button(ack, body, client, logger, context):
#     ack()
#     logger.info(body)
#     user_id = context["user_id"]
#     team_id = context["team_id"]
#     home.refresh(client, user_id, logger)

# triggers when user chooses to manager the schedule
@app.action(actions.MANAGE_SCHEDULE_ACTION)
def handle_manager_schedule_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    blocks = [
        forms.make_header_row("Choose an option to update your Schedule:"),
        forms.make_action_button_row([inputs.ADD_AO_FORM, inputs.EDIT_AO_FORM, inputs.ADD_EVENT_FORM]),
        forms.make_header_row("Choose an option to update your Recurring Events:"),
        forms.make_action_button_row([inputs.SELECT_RECURRING_EVENT_FORM, inputs.DELETE_RECURRING_EVENT_FORM]),
        forms.make_header_row("Choose an option to update your Single Events:"),
        forms.make_action_button_row([inputs.EDIT_SINGLE_EVENT_FORM, inputs.DELETE_SINGLE_EVENT_FORM]),
        forms.make_header_row("Return to the Home Page:"),
        forms.make_action_button_row([inputs.CANCEL_BUTTON])
    ]

    print(blocks)

    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)


@app.action(inputs.ADD_AO_FORM.action)
def handle_add_ao_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    ao.add_form(team_id, user_id, client, logger)

@app.action(inputs.EDIT_AO_FORM.action)
def handle_edit_ao_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    ao.edit_form(team_id, user_id, client, logger)

@app.action(inputs.ADD_EVENT_FORM.action)
def handle_add_event_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    event.add_form(team_id, user_id, client, logger)

@app.action(inputs.EDIT_SINGLE_EVENT_FORM.action)
def handle_edit_event_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    event.edit_single_form(team_id, user_id, client, logger)

@app.action(inputs.DELETE_SINGLE_EVENT_FORM.action)
def handle_delete_single_event_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    event.delete_single_form(team_id, user_id, client, logger)

@app.action(inputs.SELECT_RECURRING_EVENT_FORM.action)
def handle_edit_event_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    event.select_recurring_form_for_edit(team_id, user_id, client, logger)

@app.action(inputs.DELETE_RECURRING_EVENT_FORM.action)
def handle_delete_single_event_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    event.select_recurring_form_for_delete(team_id, user_id, client, logger)

@app.action(inputs.GENERAL_SETTINGS.action)
def handle_general_settings_form(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    settings.general_form(team_id, user_id, client, logger)

@app.action(actions.DELETE_RECURRING_SELECT_ACTION)
def handle_delete_recurring_select(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']
    input_data = body['actions'][0]['value']
    response = weekly_handler.delete(client, user_id, team_id, logger, input_data)
    home.refresh(client, user_id, logger, response.message, team_id, context)

@app.action("edit_recurring_event_slot_select")
def handle_edit_recurring_event_slot_select(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']
    print(body['actions'][0]['value'])
    selected_ao, selected_day, selected_event_type, selected_start_time, selected_end_time, selected_ao_id = str.split(body['actions'][0]['value'], '|')

    # Build options lists
    # list of AOs for dropdown
    try:
        with my_connect(team_id) as mydb:
            sql_ao_list = f"SELECT ao_display_name FROM {mydb.db}.qsignups_aos WHERE team_id = '{team_id}' ORDER BY REPLACE(ao_display_name, 'The ', '');"
            ao_list = pd.read_sql(sql_ao_list, mydb.conn)
            ao_list = ao_list['ao_display_name'].values.tolist()
    except Exception as e:
        logger.error(f"Error pulling AO list: {e}")

    ao_options = []
    for option in ao_list:
        new_option = {
            "text": {
                "type": "plain_text",
                "text": option,
                "emoji": True
            },
            "value": option
        }
        ao_options.append(new_option)
    selected_ao_index = ao_list.index(selected_ao)

    day_list = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ]
    day_options = []
    for option in day_list:
        new_option = {
            "text": {
                "type": "plain_text",
                "text": option,
                "emoji": True
            },
            "value": option
        }
        day_options.append(new_option)
    selected_day_index = day_list.index(selected_day)

    event_type_list = ['Bootcamp', 'QSource', 'Custom']
    event_type_options = []
    for option in event_type_list:
        new_option = {
            "text": {
                "type": "plain_text",
                "text": option,
                "emoji": True
            },
            "value": option
        }
        event_type_options.append(new_option)
    try:
        selected_event_type_index = event_type_list.index(selected_event_type)
    except ValueError as e:
        selected_event_type_index = -1

    if selected_end_time is None:
        selected_end_time = str(int(selected_start_time[:2]) + 1) + ':' + selected_start_time[2:]

    blocks = [
        {
            "type": "input",
            "block_id": "event_type_select",
            "element": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an event type",
                    "emoji": True
                },
                "options": event_type_options,
                "action_id": "event_type_select_action",
                "initial_option": event_type_options[selected_event_type_index]
            },
            "label": {
                "type": "plain_text",
                "text": "Event Type",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "event_type_custom",
            "element": {
                "type": "plain_text_input",
                "action_id": "event_type_custom",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Custom Event Name"
                },
                "initial_value": selected_event_type
            },
            "label": {
                "type": "plain_text",
                "text": "If Custom selected, please specify"
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "ao_display_name_select",
            "element": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an AO",
                    "emoji": True
                },
                "options": ao_options,
                "action_id": "ao_display_name_select_action",
                "initial_option": ao_options[selected_ao_index]
            },
            "label": {
                "type": "plain_text",
                "text": "AO",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "event_day_of_week_select",
            "element": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a day",
                    "emoji": True
                },
                "options": day_options,
                "action_id": "event_day_of_week_select_action",
                "initial_option": day_options[selected_day_index]
            },
            "label": {
                "type": "plain_text",
                "text": "Day of Week",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "event_start_time_select",
            "element": {
                "type": "timepicker",
                "initial_time": selected_start_time[:2] + ':' + selected_start_time[2:],
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select time",
                    "emoji": True
                },
                "action_id": "event_start_time_select"
            },
            "label": {
                "type": "plain_text",
                "text": "Event Start",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "event_end_time_select",
            "element": {
                "type": "timepicker",
                "initial_time": selected_end_time[:2] + ':' + selected_end_time[2:],
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select time",
                    "emoji": True
                },
                "action_id": "event_end_time_select"
            },
            "label": {
                "type": "plain_text",
                "text": "Event End",
                "emoji": True
            }
        },
        {
            "type": "input",
            "block_id": "add_event_datepicker",
            "element": {
                "type": "datepicker",
                "initial_date": date.today().strftime('%Y-%m-%d'),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select date",
                    "emoji": True
                },
                "action_id": "add_event_datepicker"
            },
            "label": {
                "type": "plain_text",
                "text": "Start Date",
                "emoji": True
            }
        },
        {
            "type": "actions",
            "block_id": "submit_cancel_buttons",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Submit",
                        "emoji": True
                    },
                    "value": "submit",
                    "action_id": "submit_edit_recurring_event",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Cancel",
                        "emoji": True
                    },
                    "value": "cancel",
                    "action_id": "cancel_button_select",
                    "style": "danger"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Please wait after hitting Submit, and do not hit it more than once"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": selected_ao_id + '|' + selected_day + '|' + selected_start_time
                }
            ]
        }

    ]

    if selected_end_time != 'None': blocks[5]['element']['initial_time'] = selected_start_time[:2] + ':' + selected_start_time[2:]
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)

@app.action("submit_edit_recurring_event")
def handle_edit_recurring_event(ack, body, client, logger, context):
    ack()
    logger.info(body)
    print(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    # Gather inputs from form
    input_data = body['view']['state']['values']
    ao_display_name = input_data['ao_display_name_select']['ao_display_name_select_action']['selected_option']['value']
    event_day_of_week = input_data['event_day_of_week_select']['event_day_of_week_select_action']['selected_option']['value']
    starting_date = input_data['add_event_datepicker']['add_event_datepicker']['selected_date']
    event_time = input_data['event_start_time_select']['event_start_time_select']['selected_time'].replace(':','')
    event_end_time = input_data['event_end_time_select']['event_end_time_select']['selected_time'].replace(':','')

    og_ao_channel_id, og_event_day_of_week, og_event_time = body['view']['blocks'][-1]['elements'][0]['text'].split('|')

    # Logic for custom events
    if input_data['event_type_select']['event_type_select_action']['selected_option']['value'] == 'Custom':
        event_type = input_data['event_type_custom']['event_type_custom']['value']
    else:
        event_type = input_data['event_type_select']['event_type_select_action']['selected_option']['value']

    event_recurring = True

    # Grab channel id
    try:
        with my_connect(team_id) as mydb:
            mycursor = mydb.conn.cursor()
            mycursor.execute(f'SELECT ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" AND ao_display_name = "{ao_display_name}";')
            ao_channel_id = mycursor.fetchone()[0]
    except Exception as e:
           logger.error(f"Error pulling from db: {e}")

    # Build query params
    query_params = {
        'team_id': team_id,
        'ao_channel_id': ao_channel_id,
        'event_day_of_week': event_day_of_week,
        'event_time': event_time,
        'event_end_time': event_end_time,
        'event_type': event_type,
        'event_recurring': True,
        'og_ao_channel_id': og_ao_channel_id,
        'og_event_day_of_week': og_event_day_of_week,
        'og_event_time': og_event_time,
        'starting_date': starting_date
    }

    # Update weekly table
    try:
        with my_connect(team_id) as mydb:
            sql_update = f"""-- sql
            UPDATE {mydb.db}.qsignups_weekly
            SET ao_channel_id = %(ao_channel_id)s, event_day_of_week = %(event_day_of_week)s, event_time = %(event_time)s,
                event_end_time = %(event_end_time)s, event_type = %(event_type)s, team_id = %(team_id)s
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(og_ao_channel_id)s
                AND event_day_of_week = %(og_event_day_of_week)s
                AND event_time = %(og_event_time)s
            ;
            """
            logging.info(f"Attempting SQL UPDATE: {sql_update}")

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
    except Exception as e:
           logger.error(f"Error writing to schedule_weekly: {e}")

    # Update master schedule table
    logger.info(f"Attempting SQL UPDATE into schedule_master")
    success_status = False

    # Support for changing day of week
    if event_day_of_week != og_event_day_of_week:
        day_list = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        new_dow_num = day_list.index(event_day_of_week)
        old_dow_num = day_list.index(og_event_day_of_week)
        query_params['day_adjust'] = new_dow_num - old_dow_num
    else:
        query_params['day_adjust'] = 0

    # Attempt update
    try:
        with my_connect(team_id) as mydb:

            sql_update = f"""-- sql
            UPDATE {mydb.db}.qsignups_master
            SET ao_channel_id = %(ao_channel_id)s, event_date = DATE_ADD(event_date, INTERVAL %(day_adjust)s DAY), event_day_of_week = %(event_day_of_week)s,
                event_time = %(event_time)s, event_end_time = %(event_end_time)s, event_type = %(event_type)s, team_id = %(team_id)s, event_recurring = %(event_recurring)s
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(og_ao_channel_id)s
                AND event_day_of_week = %(og_event_day_of_week)s
                AND event_time = %(og_event_time)s
                AND event_date >= DATE(%(starting_date)s)
            ;
            """

            logging.info(f"Attempting SQL UPDATE: {sql_update}")

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
           logger.error(f"Error writing to schedule_master: {e}")
           error_msg = e

    # Give status message and return to home
    if success_status:
        top_message = f"Thanks, I got it! I've made your selected changes to {event_type}s on {event_day_of_week}s at {event_time} at {ao_display_name}."
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"
    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.action("delete_single_event_ao_select")
def handle_delete_single_event_ao_select(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    ao_display_name = body['actions'][0]['selected_option']['text']['text']
    ao_channel_id = body['actions'][0]['selected_option']['value']

    # Pull upcoming schedule from db
    try:
        with my_connect(team_id) as mydb:
            # TODO: make this specific to event type
            sql_pull = f'''
            SELECT m.*, a.ao_display_name
            FROM {mydb.db}.qsignups_master m
            INNER JOIN {mydb.db}.qsignups_aos a
            ON m.ao_channel_id = a.ao_channel_id
            WHERE a.team_id = "{team_id}"
                AND a.ao_channel_id = "{ao_channel_id}"
                AND m.event_date > DATE("{date.today()}")
                AND m.event_date <= DATE("{date.today() + timedelta(weeks=12)}");
            '''
            logging.info(f'Pulling from db, attempting SQL: {sql_pull}')
            results_df = pd.read_sql_query(sql_pull, mydb.conn, parse_dates=['event_date'])
    except Exception as e:
        logger.error(f"Error pulling from schedule_master: {e}")

    # Construct view
    # Top of view
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Please select a Q slot to delete for:"}
    },
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{ao_display_name}*"}
    },
    {
        "type": "divider"
    }]

    # Show next x number of events
    # TODO: future add: make a "show more" button?
    results_df['event_date_time'] = pd.to_datetime(results_df['event_date'].dt.strftime('%Y-%m-%d') + ' ' + results_df['event_time'], infer_datetime_format=True)
    for index, row in results_df.iterrows():
        # Pretty format date
        date_fmt = row['event_date_time'].strftime("%a, %m-%d @ %H%M")
        date_fmt_value = row['event_date_time'].strftime('%Y-%m-%d %H:%M:%S')

        # Build buttons
        if row['q_pax_id'] is None:
            date_status = "OPEN!"
        else:
            date_status = row['q_pax_name']

        action_id = "delete_single_event_button"
        value = date_fmt_value + '|' + row['ao_channel_id']
        confirm_obj = {
            "title": {
                "type": "plain_text",
                "text": "Delete this event?"
            },
            "text": {
                "type": "mrkdwn",
                "text": "Are you sure you want to delete this event? This cannot be undone."
            },
            "confirm": {
                "type": "plain_text",
                "text": "Yes, delete it"
            },
            "deny": {
                "type": "plain_text",
                "text": "Cancel"
            }
        }
        # Button template
        new_button = inputs.ActionButton(
            label = f"{date_fmt}: {date_status}", value = value, action = action_id, confirm = confirm_obj)
        # Append button to list
        blocks.append(forms.make_action_button_row([new_button]))

    blocks.append(forms.make_action_button_row([inputs.CANCEL_BUTTON]))

    # Publish view
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)

@app.action("delete_single_event_button")
def delete_single_event_button(ack, client, body, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']
    # user_name = get_user_name([user_id], logger, client)

    # gather and format selected date and time
    selected_list = str.split(body['actions'][0]['value'],'|')
    selected_date = selected_list[0]
    selected_ao_id = selected_list[1]
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_date_db = datetime.date(selected_date_dt).strftime('%Y-%m-%d')
    selected_time_db = datetime.time(selected_date_dt).strftime('%H%M')

    # Build query params
    query_params = {
        'team_id': team_id,
        'ao_channel_id': selected_ao_id,
        'event_date': selected_date_db,
        'event_time': selected_time_db
    }

    # attempt delete
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            sql_delete = f"""-- sql
            DELETE FROM {mydb.db}.qsignups_master
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(ao_channel_id)s
                AND event_date = DATE(%(event_date)s)
                AND event_time = %(event_time)s;
            """
            logger.info(f'Attempting SQL: \n{sql_delete}')
            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_delete, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error pulling AO list: {e}")
        error_msg = e

    # Take the user back home
    if success_status:
        top_message = f"Success! Deleted event on {selected_date_db} at {selected_time_db}"
    else:
        top_message = f"Sorry, there was a problem of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.action("edit_ao_select")
def handle_edit_ao_select(ack, body, client, logger, context):
    ack()
    logger.info(body)
    print(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    selected_channel = body['view']['state']['values']['edit_ao_select']['edit_ao_select']['selected_option']['value']
    selected_channel_name = body['view']['state']['values']['edit_ao_select']['edit_ao_select']['selected_option']['text']['text']

    # pull existing info for this channel
    try:
        with my_connect(team_id) as mydb:
            sql_pull = f"""
            SELECT ao_display_name, ao_location_subtitle
            FROM {mydb.db}.qsignups_aos
            WHERE team_id = '{team_id}'
                AND ao_channel_id = '{selected_channel}';
            """
            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_pull)
            results = mycursor.fetchone()
            if results is None:
                results = (None, None)
            ao_display_name, ao_location_subtitle = results

            sql_ao_list = f"SELECT ao_display_name, ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = '{team_id}' ORDER BY REPLACE(ao_display_name, 'The ', '');"
            ao_list = pd.read_sql(sql_ao_list, mydb.conn)
    except Exception as e:
        logger.error(f"Error pulling AO list: {e}")

    if results is None:
        home.refresh(client, user_id, logger, top_message="Selected channel not found - PAXMiner may not have added it to the aos table yet", team_id=team_id, context=context)
    else:
        if ao_display_name is None:
            ao_display_name = ""
        if ao_location_subtitle is None:
            ao_location_subtitle = ""

        # rebuild blocks
        ao_options = []
        for index, row in ao_list.iterrows():
            new_option = {
                "text": {
                    "type": "plain_text",
                    "text": row['ao_display_name'],
                    "emoji": True
                },
                "value": row['ao_channel_id']
            }
            ao_options.append(new_option)

        blocks = [
            {
                "type": "section",
                "block_id": "page_label",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Edit AO:*\n*{selected_channel_name}*\n{selected_channel}"
			    }
            },
            {
                "type": "input",
                "block_id": "ao_display_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "ao_display_name",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Weasel's Ridge"
                    },
                    "initial_value": ao_display_name
                },
                "label": {
                    "type": "plain_text",
                    "text": "AO Title"
                }
            },
            {
                "type": "input",
                "block_id": "ao_location_subtitle",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "ao_location_subtitle",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Oompa Loompa Kingdom"
                    },
                    "initial_value": ao_location_subtitle
                },
                "label": {
                    "type": "plain_text",
                    "text": "Location (township, park, etc.)"
                }
            }
        ]
        blocks.append(forms.make_action_button_row([
            inputs.make_submit_button(actions.EDIT_AO_ACTION),
            inputs.CANCEL_BUTTON
        ]))


        try:
            client.views_publish(
                user_id=user_id,
                view={
                    "type": "home",
                    "blocks": blocks
                }
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")
            print(e)

@app.action("add_event_recurring_select_action")
def handle_add_event_recurring_select_action(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    recurring_select_option = body['view']['state']['values']['recurring_select_block']['add_event_recurring_select_action']['selected_option']
    recurring_select = recurring_select_option['value']

    logger.info('add an event - switch recurring type')

    # list of AOs for dropdown
    try:
        with my_connect(team_id) as mydb:
            sql_ao_list = f"SELECT ao_display_name FROM {mydb.db}.qsignups_aos WHERE team_id = '{team_id}' ORDER BY REPLACE(ao_display_name, 'The ', '');"
            ao_list = pd.read_sql(sql_ao_list, mydb.conn)
            ao_list = ao_list['ao_display_name'].values.tolist()
    except Exception as e:
        logger.error(f"Error pulling AO list: {e}")

    ao_selector = inputs.ActionSelector(label = "Select an AO", action = "ao_display_name_select_action", options = ao_list)

    blocks = [
        forms.make_header_row("*Is this a recurring or single event?*"),
        inputs.EVENT_TYPE_RADIO.as_form_field(initial_value = recurring_select_option),
        inputs.EVENT_TYPE_SELECTOR.as_form_field(),
        inputs.ActionInput(label = "Custom Event Name", action = "event_type_custom", placeholder = "If custom is selected, specify a name", optional = True),
        ao_selector.as_form_field(),
    ]

    if recurring_select == 'recurring':
        blocks.append(inputs.WEEKDAY_SELECTOR.as_form_field())
        blocks.append(inputs.START_DATE_SELECTOR.as_form_field(initial_value = date.today().strftime('%Y-%m-%d')))

    else:
        # TODO: have "other" / freeform option
        # TODO: add this to form
        special_list = [
            'None',
            'The Forge',
            'VQ',
            'F3versary',
            'Birthday Q',
            'AO Launch',
            'Convergence'
        ]
        special_selector = inputs.ActionSelector(label = "Event Type", action = "event_special_type_selector", options = special_list)
        blocks.append(special_selector.as_form_field())
        blocks.append(inputs.EVENT_DATE_SELECTOR.as_form_field(initial_value = date.today().strftime('%Y-%m-%d')))

    blocks += [
        inputs.START_TIME_SELECTOR.as_form_field(initial_value = "05:30"),
        inputs.END_TIME_SELECTOR.as_form_field(initial_value = "06:15"),

        forms.make_action_button_row([
            inputs.make_submit_button(actions.ADD_EVENT_ACTION).as_form_field(),
            inputs.CANCEL_BUTTON.as_form_field()
        ]),
        {
        "type": "context",
        "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Please wait after hitting Submit, and do not hit it more than once"
                }
            ]
        }
    ]

    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)

@app.action("edit_event_ao_select")
def handle_edit_event_ao_select(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    ao_display_name = body['actions'][0]['selected_option']['text']['text']
    ao_channel_id = body['actions'][0]['selected_option']['value']

    # Pull upcoming schedule from db
    try:
        with my_connect(team_id) as mydb:
            # TODO: make this specific to event type
            sql_pull = f'''
            SELECT m.*, a.ao_display_name
            FROM {mydb.db}.qsignups_master m
            INNER JOIN {mydb.db}.qsignups_aos a
            ON m.team_id = a.team_id
                AND m.ao_channel_id = a.ao_channel_id
            WHERE a.team_id = "{team_id}"
                AND a.ao_channel_id = "{ao_channel_id}"
                AND m.event_date > DATE("{date.today()}")
                AND m.event_date <= DATE("{date.today() + timedelta(weeks=12)}");
            '''
            logging.info(f'Pulling from db, attempting SQL: {sql_pull}')
            results_df = pd.read_sql_query(sql_pull, mydb.conn, parse_dates=['event_date'])
    except Exception as e:
        logger.error(f"Error pulling from schedule_master: {e}")

    # Construct view
    # Top of view
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Please select a Q slot to edit for:"}
    },
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{ao_display_name}*"}
    },
    {
        "type": "divider"
    }]

    # Show next x number of events
    results_df['event_date_time'] = pd.to_datetime(results_df['event_date'].dt.strftime('%Y-%m-%d') + ' ' + results_df['event_time'], infer_datetime_format=True)
    for index, row in results_df.iterrows():
        # Pretty format date
        date_fmt = row['event_date_time'].strftime("%a, %m-%d @ %H%M")
        date_fmt_value = row['event_date_time'].strftime('%Y-%m-%d %H:%M:%S')

        # Build buttons
        if row['q_pax_id'] is None:
            date_status = "OPEN!"
        else:
            date_status = row['q_pax_name']

        action_id = "edit_single_event_button"
        value = date_fmt_value + '|' + row['ao_display_name']

        # Button template
        new_button = {
            "type":"actions",
            "elements":[
                {
                    "type":"button",
                    "text":{
                        "type":"plain_text",
                        "text":f"{row['event_type']} {date_fmt}: {date_status}",
                        "emoji":True
                    },
                    "action_id":action_id,
                    "value":value
                }
            ]
        }

        # Append button to list
        blocks.append(new_button)

    # Cancel button
    blocks.append(forms.make_action_button_row([inputs.CANCEL_BUTTON]))

    # Publish view
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)

@app.action(actions.EDIT_AO_ACTION)
def submit_edit_ao_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    print(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    page_label = body['view']['blocks'][0]['text']['text']
    label, ao_display_name, ao_channel_id = page_label.replace('*','').split('\n')

    input_data = body['view']['state']['values']
    ao_display_name = input_data['ao_display_name']['ao_display_name']['value']
    ao_location_subtitle = input_data['ao_location_subtitle']['ao_location_subtitle']['value']

    # Update AO table
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            query_params = {
                'ao_display_name': ao_display_name,
                'ao_location_subtitle': ao_location_subtitle,
                'ao_channel_id': ao_channel_id
            }

            sql_update = f"""-- sql
            UPDATE {mydb.db}.qsignups_aos
            SET ao_display_name = %(ao_display_name)s,
                ao_location_subtitle = %(ao_location_subtitle)s
            WHERE ao_channel_id = %(ao_channel_id)s
            ;
            """
            logger.info(f"Attempting SQL UPDATE: {sql_update}")

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error writing to db: {e}")
        error_msg = e

    # Take the user back home
    if success_status:
        top_message = f"Success! Edited info for {ao_display_name}"
    else:
        top_message = f"Sorry, there was a problem of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

def safe_get(data, keys):
    try:
        result = data
        for k in keys:
            result = result[k]
        return result
    except:
        return None

@app.action(actions.EDIT_SETTINGS_ACTION)
def handle_submit_general_settings_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    # Gather inputs from form
    input_data = body['view']['state']['values']
    response = settings_handler.update(client, user_id, team_id, logger, input_data)
    # Take the user back home
    if response.success:
        top_message = f"Success! Changed general region settings"
    else:
        top_message = f"Sorry, there was a problem of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{response.message}"
    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.action(actions.ADD_AO_ACTION)
def handle_submit_add_ao_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    print(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    # Gather inputs from form
    input_data = body['view']['state']['values']
    ao_channel_id = input_data['add_ao_channel_select']['add_ao_channel_select']['selected_channel']
    ao_display_name = input_data['ao_display_name']['ao_display_name']['value']
    ao_location_subtitle = input_data['ao_location_subtitle']['ao_location_subtitle']['value']

    # Gather inputs from form
    input_data = body['view']['state']['values']

    query_params = {
        'team_id': team_id
    }

    query_params['ao_channel_id'] = safe_get(input_data, ['add_ao_channel_select','add_ao_channel_select','selected_channel'])
    query_params['ao_display_name'] = safe_get(input_data, ['ao_display_name','ao_display_name','value'])
    query_params['ao_location_subtitle'] = safe_get(input_data, ['ao_location_subtitle','ao_location_subtitle','value'])

    # replace double quotes with single quotes
    query_params['ao_display_name'] = query_params['ao_display_name'].replace('"',"'")
    if query_params['ao_location_subtitle']:
        query_params['ao_location_subtitle'] = query_params['ao_location_subtitle'].replace('"',"'")
    else:
        query_params['ao_location_subtitle'] = '' # TODO: I don't like this, but this field is currently non-nullable

    print("FOUND GPARAMS ", query_params)

    # Update db
    success_status = False
    try:
        with my_connect(team_id) as mydb:

            sql_insert = f"""
            INSERT INTO {mydb.db}.qsignups_aos (ao_channel_id, ao_display_name, ao_location_subtitle, team_id)
            VALUES (%(ao_channel_id)s, %(ao_display_name)s, %(ao_location_subtitle)s, %(team_id)s);
            """
            print("SQL: ", sql_insert)

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_insert, query_params)
            mydb.conn.commit()
            success_status = True

    except Exception as e:
        logger.error(f"Error writing to db: {e}")
        error_msg = e

    # Take the user back home
    if success_status:
        top_message = f"Success! Added {ao_display_name} to the list of AOs on the schedule"
    else:
        top_message = f"Sorry, there was a problem of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.action(actions.ADD_EVENT_ACTION)
def handle_submit_add_event_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    # Gather inputs from form
    input_data = body['view']['state']['values']
    ao_display_name = safe_get(input_data, ['ao_display_name_select','ao_display_name_select_action','selected_option','value'])
    event_day_of_week = safe_get(input_data, ['event_day_of_week_select','event_day_of_week_select_action','selected_option','value'])
    starting_date = safe_get(input_data, ['add_event_datepicker','add_event_datepicker','selected_date'])
    event_time = safe_get(input_data, ['event_start_time_select','event_start_time_select','selected_time']).replace(':','')
    event_end_time = safe_get(input_data, ['event_end_time_select','event_end_time_select','selected_time']).replace(':','')
    event_type_select = safe_get(input_data, ['event_type_select','event_type_select_action','selected_option','value'])
    event_type_custom = safe_get(input_data, ['event_type_custom','event_type_custom','value'])

    # Logic for custom events
    if event_type_select == 'Custom':
        event_type = event_type_custom
    else:
        event_type = event_type_select

    # Grab channel id
    try:
        with my_connect(team_id) as mydb:
            mycursor = mydb.conn.cursor()
            mycursor.execute(f'SELECT ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" AND ao_display_name = "{ao_display_name}";')
            ao_channel_id = mycursor.fetchone()[0]
    except Exception as e:
           logger.error(f"Error pulling from db: {e}")

    # Build query_params
    query_params = {
        'team_id': team_id,
        'ao_channel_id': ao_channel_id,
        'event_day_of_week': event_day_of_week,
        'event_time': event_time,
        'event_end_time': event_end_time,
        'event_type': event_type,
        'event_recurring': True
    }

    # Write to weekly table
    try:
        with my_connect(team_id) as mydb:

            sql_insert = f"""
            INSERT INTO {mydb.db}.qsignups_weekly (ao_channel_id, event_day_of_week, event_time, event_end_time, event_type, team_id)
            VALUES (%(ao_channel_id)s, %(event_day_of_week)s, %(event_time)s, %(event_end_time)s, %(event_type)s, %(team_id)s);
            """
            logger.info(f"Attempting SQL INSERT: {sql_insert}")

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_insert, query_params)
            mydb.conn.commit()
    except Exception as e:
           logger.error(f"Error writing to db: {e}")

    # Write to master schedule table
    logger.info(f"Attempting SQL INSERT into schedule_master")
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            mycursor = mydb.conn.cursor()
            iterate_date = datetime.strptime(starting_date, '%Y-%m-%d').date()
            while iterate_date < (date.today() + timedelta(days=schedule_create_length_days)):
                if iterate_date.strftime('%A') == event_day_of_week:
                    query_params['event_date'] = iterate_date
                    sql_insert = f"""
                    INSERT INTO {mydb.db}.qsignups_master (ao_channel_id, event_date, event_time, event_end_time, event_day_of_week, event_type, event_recurring, team_id)
                    VALUES (%(ao_channel_id)s, DATE(%(event_date)s), %(event_time)s, %(event_end_time)s, %(event_day_of_week)s, %(event_type)s, %(event_recurring)s, %(team_id)s)
                    """
                    mycursor.execute(sql_insert, query_params)
                    # print(sql_insert)
                iterate_date += timedelta(days=1)

            mydb.conn.commit()
            success_status = True
    except Exception as e:
           logger.error(f"Error writing to schedule_master: {e}")
           error_msg = e

    # Give status message and return to home
    if success_status:
        top_message = f"Thanks, I got it! I've added {round(schedule_create_length_days/365)} year's worth of {event_type}s to the schedule for {event_day_of_week}s at {event_time} at {ao_display_name}."
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"
    home.refresh(client, user_id, logger, top_message, team_id, context)

@app.action(actions.ADD_SINGLE_EVENT_ACTION)
def handle_submit_add_single_event_button(ack, body, client, logger, context):
    ack()
    logger.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]

    # Gather inputs from form
    input_data = body['view']['state']['values']
    ao_display_name = input_data['ao_display_name_select']['ao_display_name_select_action']['selected_option']['value']
    event_date = input_data['add_event_datepicker']['add_event_datepicker']['selected_date']
    event_time = input_data['event_start_time_select']['event_start_time_select']['selected_time'].replace(':','')
    event_end_time = input_data['event_end_time_select']['event_end_time_select']['selected_time'].replace(':','')

    # Logic for custom events
    if input_data['event_type_select']['event_type_select_action']['selected_option']['value'] == 'Custom':
        event_type = input_data['event_type_custom']['event_type_custom']['value']
    else:
        event_type = input_data['event_type_select']['event_type_select_action']['selected_option']['value']

    # Grab channel id
    try:
        with my_connect(team_id) as mydb:
            mycursor = mydb.conn.cursor()
            mycursor.execute(f'SELECT ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" AND ao_display_name = "{ao_display_name}";')
            ao_channel_id = mycursor.fetchone()[0]
    except Exception as e:
           logger.error(f"Error pulling from db: {e}")

    # Build query_params
    query_params = {
        'team_id': team_id,
        'ao_channel_id': ao_channel_id,
        'event_date': event_date,
        'event_day_of_week': datetime.strptime(event_date, '%Y-%m-%d').date().strftime('%A'),
        'event_time': event_time,
        'event_end_time': event_end_time,
        'event_type': event_type,
        'event_recurring': False
    }

    # Write to master schedule table
    logger.info(f"Attempting SQL INSERT into schedule_master")
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            mycursor = mydb.conn.cursor()
            sql_insert = f"""
            INSERT INTO {mydb.db}.qsignups_master (ao_channel_id, event_date, event_time, event_end_time, event_day_of_week, event_type, event_recurring, team_id)
            VALUES (%(ao_channel_id)s, DATE(%(event_date)s), %(event_time)s, %(event_end_time)s, %(event_day_of_week)s, %(event_type)s, %(event_recurring)s, %(team_id)s);
            """

            mycursor.execute(sql_insert, query_params)
            mydb.conn.commit()
            success_status = True

    except Exception as e:
           logger.error(f"Error writing to schedule_master: {e}")
           error_msg = e

    # Give status message and return to home
    if success_status:
        top_message = f"Thanks, I got it! I've added your event to the schedule for {event_date} at {event_time} at {ao_display_name}."
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"
    home.refresh(client, user_id, logger, top_message, team_id, context)


# triggered when user makes an ao selection
@app.action("ao-select")
def ao_select_slot(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)

    user_id = context["user_id"]
    team_id = context["team_id"]
    ao_display_name = body['actions'][0]['selected_option']['text']['text']
    ao_channel_id = body['actions'][0]['selected_option']['value']

    # Pull upcoming schedule from db
    try:
        with my_connect(team_id) as mydb:
            # TODO: make this specific to event type
            sql_pull = f"""
            SELECT *
            FROM {mydb.db}.qsignups_master
            WHERE team_id = '{team_id}'
                AND ao_channel_id = '{ao_channel_id}'
                AND event_date > DATE('{date.today()}')
                AND event_date <= DATE('{date.today() + timedelta(weeks=10)}');
            """
            logging.info(f'Pulling from db, attempting SQL: {sql_pull}')

            results_df = pd.read_sql_query(sql_pull, mydb.conn, parse_dates=['event_date'])
    except Exception as e:
        logger.error(f"Error pulling from schedule_master: {e}")

    # Construct view
    # Top of view
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Please select an open Q slot for:"}
    },
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{ao_display_name}*"}
    },
    {
        "type": "divider"
    }]

    # Show next x number of events
    results_df['event_date_time'] = pd.to_datetime(results_df['event_date'].dt.strftime('%Y-%m-%d') + ' ' + results_df['event_time'], infer_datetime_format=True)
    for index, row in results_df.iterrows():
        # Pretty format date
        date_fmt = row['event_date_time'].strftime("%a, %m-%d @ %H%M")

        # If slot is empty, show green button with primary (green) style button
        if row['q_pax_id'] is None:
            date_status = "OPEN!"
            date_style = "primary"
            action_id = "date_select_button"
            value = str(row['event_date_time'])
            button_text = "Take slot"
        # Otherwise default (grey) button, listing Qs name
        else:
            date_status = row['q_pax_name']
            date_style = "default"
            action_id = "taken_date_select_button"
            value = str(row['event_date_time']) + '|' + row['q_pax_name']
            button_text = "Edit Slot"

        # try:
        #     date_status_format = re.sub('\s\(([\s\S]*?\))','',date_status)
        #     print(f"formatted: {date_status_format}")
        # except Exception as e:
        #     print(e)

        # Button template
        new_section = {
            "type":"section",
            "text":{
                "type":"mrkdwn",
                "text":f"{row['event_type']} {date_fmt}: {date_status}"
            },
            "accessory":{
                "type":"button",
                "text":{
                    "type":"plain_text",
                    "text":button_text,
                    "emoji":True
                },
                "action_id":action_id,
                "value":value
            }
        }
        if date_style == "primary":
            new_section["accessory"]["style"] = "primary"

        # Append button to list
        blocks.append(new_section)

        # new_button = {
        #     "type":"actions",
        #     "elements":[
        #         {
        #             "type":"button",
        #             "text":{
        #                 "type":"plain_text",
        #                 "text":f"{row['event_type']} {date_fmt}: {date_status}",
        #                 "emoji":True
        #             },
        #             "action_id":action_id,
        #             "value":value
        #         }
        #     ]
        # }
        # if date_style == "primary":
        #     new_button['elements'][0]["style"] = "primary"

        # # Append button to list
        # blocks.append(new_button)

    # Cancel button
    blocks.append(forms.make_action_button_row([inputs.CANCEL_BUTTON]))

    # Publish view
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)

# triggered when user selects open slot
@app.action("date_select_button")
def handle_date_select_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    logging.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    user_name = get_user_name([user_id], logger, client)

    # gather and format selected date and time
    selected_date = body['actions'][0]['value']
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_date_db = datetime.date(selected_date_dt).strftime('%Y-%m-%d')
    selected_time_db = datetime.time(selected_date_dt).strftime('%H%M')

    # gather info needed for message and SQL
    ao_display_name = body['view']['blocks'][1]['text']['text'].replace('*','')

    try:
        with my_connect(team_id) as mydb:
            sql_channel_pull = f'SELECT ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" and ao_display_name = "{ao_display_name}";'
            ao_channel_id = pd.read_sql_query(sql_channel_pull, mydb.conn).iloc[0,0]
    except Exception as e:
        logger.error(f"Error pulling channel id: {e}")

    query_params = {
        'user_id': user_id,
        'user_name': user_name,
        'team_id': team_id,
        'ao_channel_id': ao_channel_id,
        'event_date': selected_date_db,
        'event_time': selected_time_db
    }

    # Attempt db update
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            sql_update = \
            f"""-- sql
            UPDATE {mydb.db}.qsignups_master
            SET q_pax_id = %(user_id)s
                , q_pax_name = %(user_name)s
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(ao_channel_id)s
                AND event_date = DATE(%(event_date)s)
                AND event_time = %(event_time)s
            ;
            """
            logging.info(f'Attempting SQL UPDATE: {sql_update}')

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        error_msg = e

    # Generate top message and go back home
    if success_status:
        top_message = f"Got it, {user_name}! I have you down for the Q at *{ao_display_name}* on *{selected_date_dt.strftime('%A, %B %-d @ %H%M')}*"
        # TODO: if selected date was in weinke range (current or next week), update local weinke png
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

# triggered when user selects open slot on a message
@app.action("date_select_button_from_message")
def handle_date_select_button_from_message(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    logging.info(body)
    user_id = context["user_id"]
    team_id = context["team_id"]
    user_name = get_user_name([user_id], logger, client)

    # gather and format selected date and time
    selected_date = body['actions'][0]['value']
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_date_db = datetime.date(selected_date_dt).strftime('%Y-%m-%d')
    selected_time_db = datetime.time(selected_date_dt).strftime('%H%M')

    # gather info needed for message and SQL
    ao_channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    message_blocks = body['message']['blocks']

    try:
        with my_connect(team_id) as mydb:
            sql_channel_pull = f'SELECT ao_display_name FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" and ao_channel_id = "{ao_channel_id}";'
            ao_name = pd.read_sql_query(sql_channel_pull, mydb.conn).iloc[0,0]
    except Exception as e:
        logger.error(f"Error pulling channel id: {e}")

    # Build query params
    query_params = {
        'team_id': team_id,
        'user_id': user_id,
        'user_name': user_name,
        'ao_channel_id': ao_channel_id,
        'event_date': selected_date_db,
        'event_time': selected_time_db
    }

    # Attempt db update
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            sql_update = \
            f"""-- sql
            UPDATE {mydb.db}.qsignups_master
            SET q_pax_id = %(user_id)s
                , q_pax_name = %(user_name)s
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(ao_channel_id)s
                AND event_date = DATE(%(event_date)s)
                AND event_time = %(event_time)s
            ;
            """
            logging.info(f'Attempting SQL UPDATE: {sql_update}')

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        error_msg = e

    # Update original message
    open_count = 0
    block_num = -1
    if success_status:
        for counter, block in enumerate(message_blocks):
            print(f"comparing {safe_get(block, 'accessory', 'value')} and {selected_date}")
            if safe_get(block, 'accessory', 'value') == selected_date:
                block_num = counter

            if safe_get(block, 'accessory', 'text', 'text'):
                if block['accessory']['text']['text'][-5] == 'OPEN!':
                    open_count += 1

        print(block_num)
        if block_num >= 0:
            message_blocks[block_num]['text']['text'] = message_blocks[block_num]['text']['text'].replace('OPEN!', user_name)
            message_blocks[block_num]['accessory']['action_id'] = 'ignore_button'
            message_blocks[block_num]['accessory']['value'] = selected_date + '|' + user_name
            message_blocks[block_num]['accessory']['text']['text'] = user_name
            del(message_blocks[block_num]['accessory']['style'])

            # update top message
            open_count += -1
            if open_count == 1:
                open_msg = ' I see there is an open spot - who wants it?'
            elif open_count > 1:
                open_msg = ' I see there are some open spots - who wants them?'
            else:
                open_msg = ''

            message_blocks[0]['text']['text'] = f"Hello HIMs of {ao_name}! Here is your Q lineup for the week.{open_msg}"

            # publish update
            logging.info(f'sending blocks:\n{message_blocks}')
            client.chat_update(channel=ao_channel_id, ts=message_ts, blocks = message_blocks)

# triggered when user selects closed slot on a message
@app.action("ignore_button")
def handle_ignore_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()

# triggered when user selects an already-taken slot
@app.action("taken_date_select_button")
def handle_taken_date_select_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)

    # Get user id / name / admin status
    user_id = context["user_id"]
    team_id = context["team_id"]
    user_info_dict = client.users_info(user=user_id)
    user_name = safe_get(user_info_dict, 'user', 'profile', 'display_name') or safe_get(
            user_info_dict, 'user', 'profile', 'real_name') or None
    user_admin = user_info_dict['user']['is_admin']

    selected_value = body['actions'][0]['value']
    selected_list = str.split(selected_value, '|')
    selected_date = selected_list[0]
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_user = selected_list[1]
    selected_ao = body['view']['blocks'][1]['text']['text'].replace('*','')


    if (user_name == selected_user) or user_admin:
        label = 'yourself' if user_name == selected_user else selected_user
        label2 = 'myself' if user_name == selected_user else selected_user
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Would you like to edit or clear this slot?"
                }
            },
            {
                "type":"actions",
                "elements":[
                    {
                        "type":"button",
                        "text":{
                            "type":"plain_text",
                            "text":f"Edit this event",
                            "emoji":True
                        },
                        "value":f"{selected_date}|{selected_ao}",
                        "action_id":"edit_single_event_button"
                    }
                ]
            },
            {
                "type":"actions",
                "elements":[
                    {
                        "type":"button",
                        "text":{
                            "type":"plain_text",
                            "text":f"Take {label2} off this Q slot",
                            "emoji":True
                        },
                        "value":f"{selected_date}|{selected_ao}",
                        "action_id":"clear_slot_button",
                        "style":"danger"
                    }
                ]
            },
            forms.make_action_button_row([inputs.CANCEL_BUTTON])
        ]

        # Publish view
        try:
            client.views_publish(
                user_id=user_id,
                view={
                    "type": "home",
                    "blocks": blocks
                }
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")
            print(e)
    # Check to see if user matches selected user id OR if they are an admin
    # If so, bring up buttons:
    #   block 1: drop down to add special qualifier (VQ, Birthday Q, F3versary, Forge, etc.)
    #   block 2: danger button to take Q off slot
    #   block 3: cancel button that takes the user back home


@app.action("edit_single_event_button")
def handle_edit_single_event_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']
    # user_name = get_user_name([user_id], logger, client)

    # gather and format selected date and time
    selected_list = str.split(body['actions'][0]['value'],'|')
    selected_date = selected_list[0]
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_date_db = datetime.date(selected_date_dt).strftime('%Y-%m-%d')
    selected_time_db = datetime.time(selected_date_dt).strftime('%H%M')

    # gather info needed for input form
    ao_display_name = selected_list[1]

    try:
        with my_connect(team_id) as mydb:
            sql_channel_pull = f'''
            SELECT m.q_pax_id, m.q_pax_name, m.event_special, m.ao_channel_id
            FROM {mydb.db}.qsignups_master m
            INNER JOIN {mydb.db}.qsignups_aos a
            ON m.team_id = a.team_id
                AND m.ao_channel_id = a.ao_channel_id
            WHERE a.team_id = "{team_id}"
                AND a.ao_display_name = "{ao_display_name}"
                AND m.event_date = DATE("{selected_date_db}")
                AND m.event_time = "{selected_time_db}"
            ;
            '''
            result_df = pd.read_sql_query(sql_channel_pull, mydb.conn)
    except Exception as e:
        logger.error(f"Error pulling event info: {e}")

    q_pax_id = result_df.loc[0,'q_pax_id']
    q_pax_name = result_df.loc[0,'q_pax_name']
    event_special = result_df.loc[0,'event_special']
    ao_channel_id = result_df.loc[0,'ao_channel_id']

    # build special qualifier
    # TODO: have "other" / freeform option
    special_list = [
        'None',
        'The Forge',
        'VQ',
        'F3versary',
        'Birthday Q',
        'AO Launch'
    ]
    special_options = []
    for option in special_list:
        new_option = {
            "text": {
                "type": "plain_text",
                "text": option,
                "emoji": True
            },
            "value": option
        }
        special_options.append(new_option)

    if event_special in special_list:
        initial_special = special_options[special_list.index(event_special)]
    else:
        initial_special = special_options[0]

    user_select_element = {
        "type": "multi_users_select",
        "placeholder": {
            "type": "plain_text",
            "text": "Select the Q",
            "emoji": True
        },
        "action_id": "edit_event_q_select",
        "max_selected_items": 1
    }
    if q_pax_id is not None:
        user_select_element['initial_users'] = [q_pax_id]

    # Build blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Editing info for:\n{selected_date_db} @ {selected_time_db} @ {ao_display_name}\nQ: {q_pax_name}"
            }
        },
        {
			"type": "input",
            "block_id": "edit_event_datepicker",
			"element": {
				"type": "datepicker",
				"initial_date": selected_date_dt.strftime('%Y-%m-%d'),
				"placeholder": {
					"type": "plain_text",
					"text": "Select date",
					"emoji": True
				},
				"action_id": "edit_event_datepicker"
			},
			"label": {
				"type": "plain_text",
				"text": "Event Date",
				"emoji": True
			}
		},
		{
			"type": "input",
            "block_id": "edit_event_timepicker",
			"element": {
				"type": "timepicker",
				"initial_time": datetime.time(selected_date_dt).strftime('%H:%M'),
				"placeholder": {
					"type": "plain_text",
					"text": "Select time",
					"emoji": True
				},
				"action_id": "edit_event_timepicker"
			},
			"label": {
				"type": "plain_text",
				"text": "Event Time",
				"emoji": True
			}
		},
        {
			"type": "input",
            "block_id": "edit_event_q_select",
			"element": user_select_element,
			"label": {
				"type": "plain_text",
				"text": "Q",
				"emoji": True
			}
		},
        {
            "type": "input",
            "block_id": "edit_event_special_select",
            "element": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Special event?",
                    "emoji": True
                },
                "options": special_options,
                "initial_option": initial_special,
                "action_id": "edit_event_special_select"
            },
            "label": {
                "type": "plain_text",
                "text": "Special Event Qualifier",
                "emoji": True
            }
        }
    ]

    # Sumbit / Cancel buttons
    submit_button = inputs.ActionButton(
        label = 'Submit', style = 'primary', value = ao_channel_id, action = actions.EDIT_EVENT_ACTION)
    blocks.append(forms.make_action_button_row([submit_button, inputs.CANCEL_BUTTON]))

    # Publish view
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        print(e)


# triggered when user hits submit on event edit
@app.action(actions.EDIT_EVENT_ACTION)
def handle_submit_edit_event_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']

    # gather inputs
    original_info = body['view']['blocks'][0]['text']['text']
    ignore, event, q_name = original_info.split('\n')
    original_date, original_time, original_ao_name = event.split(' @ ')
    original_channel_id = body['actions'][0]['value']

    results = body['view']['state']['values']
    selected_date = results['edit_event_datepicker']['edit_event_datepicker']['selected_date']
    selected_time = results['edit_event_timepicker']['edit_event_timepicker']['selected_time'].replace(':','')
    selected_q_id_list = results['edit_event_q_select']['edit_event_q_select']['selected_users']
    if len(selected_q_id_list) == 0:
        selected_q_id_fmt = None
        selected_q_name_fmt = None
    else:
        selected_q_id = selected_q_id_list[0]
        user_info_dict = client.users_info(user=selected_q_id)
        selected_q_name = safe_get(user_info_dict, 'user', 'profile', 'display_name') or safe_get(
            user_info_dict, 'user', 'profile', 'real_name') or None

        selected_q_id_fmt = selected_q_id
        selected_q_name_fmt = selected_q_name
    selected_special = results['edit_event_special_select']['edit_event_special_select']['selected_option']['text']['text']
    if selected_special == 'None':
        selected_special_fmt = None
    else:
        selected_special_fmt = selected_special

    # Build query params
    query_params = {
        'q_pax_id': selected_q_id_fmt,
        'q_pax_name': selected_q_name_fmt,
        'event_date': selected_date,
        'event_time': selected_time,
        'event_special': selected_special_fmt,
        'team_id': team_id,
        'og_ao_channel_id': original_channel_id,
        'og_event_date': original_date,
        'og_event_time': original_time
    }

    # Attempt db update
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            sql_update = \
            f"""-- sql
            UPDATE {mydb.db}.qsignups_master
            SET q_pax_id = %(q_pax_id)s
                , q_pax_name = %(q_pax_name)s
                , event_date = DATE(%(event_date)s)
                , event_time = %(event_time)s
                , event_special = %(event_special)s
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(og_ao_channel_id)s
                AND event_date = DATE(%(og_event_date)s)
                AND event_time = %(og_event_time)s
            ;
            """
            logging.info(f'Attempting SQL UPDATE: {sql_update}')

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        error_msg = e

    # Generate top message and go back home
    if success_status:
        top_message = f"Got it! I've edited this slot with the following values: {selected_date} @ {selected_time} @ {original_ao_name} - Q: {selected_q_name_fmt} - Special: {selected_special}."
        # TODO: if selected date was in weinke range (current or next week), update local weinke png
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

# triggered when user hits cancel or some other button that takes them home
@app.action("clear_slot_button")
def handle_clear_slot_button(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    logger.info(body)
    user_id = context['user_id']
    team_id = context['team_id']
    user_name = get_user_name([user_id], logger, client)

    # gather and format selected date and time
    selected_list = str.split(body['actions'][0]['value'],'|')
    selected_date = selected_list[0]
    selected_date_dt = datetime.strptime(selected_date, '%Y-%m-%d %H:%M:%S')
    selected_date_db = datetime.date(selected_date_dt).strftime('%Y-%m-%d')
    selected_time_db = datetime.time(selected_date_dt).strftime('%H%M')

    # gather info needed for message and SQL
    ao_display_name = selected_list[1]

    try:
        with my_connect(team_id) as mydb:
            sql_channel_pull = f'SELECT ao_channel_id FROM {mydb.db}.qsignups_aos WHERE team_id = "{team_id}" AND ao_display_name = "{ao_display_name}";'
            ao_channel_id = pd.read_sql_query(sql_channel_pull, mydb.conn).iloc[0,0]
    except Exception as e:
        logger.error(f"Error pulling channel id: {e}")

    # Build query params
    query_params = {
        'team_id': team_id,
        'ao_channel_id': ao_channel_id,
        'event_date': selected_date_db,
        'event_time': selected_time_db
    }

    # Attempt db update
    success_status = False
    try:
        with my_connect(team_id) as mydb:
            sql_update = \
            f"""-- sql
            UPDATE {mydb.db}.qsignups_master
            SET q_pax_id = NULL
                , q_pax_name = NULL
            WHERE team_id = %(team_id)s
                AND ao_channel_id = %(ao_channel_id)s
                AND event_date = DATE(%(event_date)s)
                AND event_time = %(event_time)s
            ;
            """
            logging.info(f'Attempting SQL UPDATE: {sql_update}')

            mycursor = mydb.conn.cursor()
            mycursor.execute(sql_update, query_params)
            mydb.conn.commit()
            success_status = True
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        error_msg = e

    # Generate top message and go back home
    if success_status:
        top_message = f"Got it, {user_name}! I have cleared the Q slot at *{ao_display_name}* on *{selected_date_dt.strftime('%A, %B %-d @ %H%M')}*"
        # TODO: if selected date was in weinke range (current or next week), update local weinke png
    else:
        top_message = f"Sorry, there was an error of some sort; please try again or contact your local administrator / Weasel Shaker. Error:\n{error_msg}"

    home.refresh(client, user_id, logger, top_message, team_id, context)

# triggered when user hits cancel or some other button that takes them home
@app.action(actions.CANCEL_BUTTON_ACTION)
def cancel_button_select(ack, client, body, logger, context):
    # acknowledge action and log payload
    ack()
    # print('Logging body and context:')
    # logging.info(body)
    # logging.info(context)
    user_id = context['user_id']
    team_id = context['team_id']
    user_name = get_user_name([user_id], logger, client)
    top_message = f"Welcome to QSignups, {user_name}!"
    home.refresh(client, user_id, logger, top_message, team_id, context)


SlackRequestHandler.clear_all_log_handlers()
logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)
# logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


def handler(event, context):
    print(f'Original event: {event}')
    print(f'Original context: {context}')
    # parsed_event = json.loads(event['body'])
    # team_id = parsed_event['team_id']
    # print(f'Team ID: {team_id}')
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

# # -- OAuth flow -- #
# export SLACK_SIGNING_SECRET=***
# export SLACK_BOT_TOKEN=xoxb-***
# export SLACK_CLIENT_ID=111.111
# export SLACK_CLIENT_SECRET=***
# export SLACK_SCOPES=app_mentions:read,chat:write

# AWS IAM Role: bolt_python_s3_storage
#   - AmazonS3FullAccess
#   - AWSLambdaBasicExecutionRole

# rm -rf latest_slack_bolt && cp -pr ../../src latest_slack_bolt
# pip install python-lambda
# lambda deploy --config-file aws_lambda_oauth_config.yaml --requirements requirements_oauth.txt

if __name__ == "__main__":
  app.start( port=int(os.environ.get("PORT", 3000)))
