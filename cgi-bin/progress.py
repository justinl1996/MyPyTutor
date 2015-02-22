#!/usr/bin/env python

import cgi
import datetime
import os

from mako.template import Template
from mako import exceptions

from admin import ADMINS, UNAUTHORISED
import uqauth
import support


DATE_FORMAT = '%d/%m/%Y %I:%M%p'
TZ_DELTA = datetime.timedelta(hours=10)


def get_submissions(user):
    """Return a list of submission statistics for the given user."""
    # get the raw data
    tutorials = support.get_tutorials()
    all_submissions = support.parse_submission_log(user)

    # create a list containing either submission date or None for each tutorial
    submissions = []
    for tut in tutorials:
        sub = [s for s in all_submissions if s.hash == tut.hash]
        submissions.append(sub[0] if sub else None)

    return zip(tutorials, submissions)


def process_tutorial(tutorial, submission):
    if submission is None or submission.date is None:
        status = 'unsubmitted'
    elif submission.date <= tutorial.due:
        status = 'submitted'
    elif submission.allow_late:
        status = 'late_ok'
    else:
        status = 'late'

    submit = (submission and submission.date and
              (submission.date + TZ_DELTA).strftime(DATE_FORMAT))

    return {
        'hash': tutorial.hash,
        'slug': tutorial.tutorial_name,
        'title': tutorial.tutorial_name.replace('_', ' '),
        'status': status,
        'submit_time': submit,
        'has_allow_late': submission is not None and submission.allow_late,
    }


def main():
    try:
        this_user = uqauth.get_user()
    except uqauth.Redirected:
        return

    form = cgi.FieldStorage(keep_blank_values=True)
    is_admin = (this_user in ADMINS)

    user = form.getvalue('user', this_user)
    if user != this_user and not is_admin:
        print UNAUTHORISED.format(this_user)
        return

    message = None
    if (is_admin and os.environ.get('REQUEST_METHOD') == 'POST' and
            'action' in form):
        if form.getvalue('action') == 'allow_late':
            action = (lambda tutorial:
                      support.set_allow_late(user, tutorial, this_user, True))
            message = ('alert-info', 'Student will now gain credit for late '
                       'submissions to the selected problems.')
        elif form.getvalue('action') == 'disallow_late':
            action = (lambda tutorial:
                      support.set_allow_late(user, tutorial, this_user, False))
            message = ('alert-info', 'Student will now be penalised for late '
                       'submissions to the selected problems.')
        else:
            action = None
            message = ('alert-danger', 'Action unknown or not specified.')

        problems = form.getlist('problem')
        if action and problems:
            map(action, problems)
        elif action and not problems:
            message = ('alert-warning', 'No problems specified.')


    user_info = (support.get_user(user) or
                 support.User(user, 'UNKNOWN', 'UNKNOWN', 'not_enrolled'))
    submissions = get_submissions(user)

    print "Content-Type: text/html\n"

    data = {
        'name': 'Change Me',
        'id': 'changeme',
        'user': user_info,
        'openIndex': 0,
        'is_admin': is_admin,
        'message': message,
    };

    # Count the number of on-time or accepted-late submissions the student has made.
    data['mark'] = 0
    data['late'] = 0

    data['groups'] = []
    group = None

    for tutorial, submission in submissions:
        if not group or tutorial.problem_set_name != group['slug']:
            group = {
                'slug': tutorial.problem_set_name,
                'title': tutorial.problem_set_name.replace('_', ' '),
                'due': (tutorial.due + TZ_DELTA).strftime(DATE_FORMAT),
                'problems': []
            }

            data['groups'].append(group)

        group['problems'].append(process_tutorial(tutorial, submission))

        if (submission is not None and submission.date is not None and
                (submission.date <= tutorial.due or submission.allow_late)):
            data['mark'] += 1
        elif submission is not None and submission.date is not None:
            data['late'] += 1

    data['total'] = len(submissions)

    try:
        print(Template(filename="./templates/progress.html").render(**data))
    except:
        print(exceptions.html_error_template().render())

if __name__ == '__main__':
    main()
