from datetime import timedelta

from django.db import models
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

from system.models import Post

from grading.models import ScoringScript, DataGrader, Submission, \
    request_submission_grading, request_qs_grading


class Contest(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.ForeignKey('system.Post', related_name='+')
    rules = models.ForeignKey('system.Post', related_name='+')
    scoring_script = models.ForeignKey('grading.ScoringScript')
    verification_stage = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    test_stage = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    bigger_better = models.BooleanField(default=True)
    observing = models.ManyToManyField('auth.User',
        related_name='observed_contests')

    def __repr__(self):
        return "<Contest " + "\"" + self.code + "\">"

    def __str__(self):
        return self.code


def is_contest_admin(user, contest):
    return user is not None and user.is_superuser


class ContestFactory(object):
    """
    Creates and updates a contest, with all the related objects.

    It presents simple, flat interface for creating and modifying contests.
    May seem repetitive, but it is crucial to keep views clean and it
    helps with testing.
    """
    # TODO "automate" some trivial parts
    name = None
    code = None
    description = None
    rules = None
    scoring_script = None
    bigger_better = None
    verification_begin = None
    verification_end = None
    answer_for_verification = None
    test_begin = None
    test_end = None
    answer_for_test = None
    published_final_results = None
    selected_limit = None

    # TODO maybe move out of class. It is a proxy between ContestForm and this.
    @classmethod
    def from_dict(cls, data):
        factory = cls()
        factory.name = data.get('name')
        factory.code = data.get('code')
        factory.description = data.get('description')
        factory.rules = data.get('rules')
        factory.scoring_script = data.get('scoring_script')
        factory.bigger_better = data.get('bigger_better')
        factory.answer_for_verification = data.get('answer_for_verification')
        factory.verification_begin = data.get('verification_begin')
        factory.verification_end = data.get('verification_end')
        factory.answer_for_test = data.get('answer_for_test')
        factory.test_begin = data.get('test_begin')
        factory.test_end = data.get('test_end')
        factory.published_final_results = data.get('published_final_results')
        factory.selected_limit = data.get('selected_limit')
        return factory

    @transaction.atomic
    def create(self):
        # Builds the contest structure then updates with data
        description = Post()
        description.save()
        rules = Post()
        rules.save()
        scoring_script = ScoringScript()
        scoring_script.save()
        contest = Contest(
            name=self.name,
            code=self.code,
            description=description,
            rules=rules,
            scoring_script=scoring_script,
        )
        contest.save()
        verification_stage = ContestStage()
        verification_stage.contest = contest
        verification_stage.begin = timezone.now()
        verification_stage.end = timezone.now()
        verification_stage.requires_selection = False
        verification_stage.published_results = True
        verification_grader = DataGrader.create(scoring_script, None)
        verification_grader.save()
        verification_stage.grader = verification_grader
        verification_stage.save()
        test_stage = ContestStage()
        test_stage.contest = contest
        test_stage.begin = timezone.now()
        test_stage.end = timezone.now()
        test_stage.requires_selection = True
        test_stage.published_results = False
        test_grader = DataGrader.create(scoring_script, None)
        test_grader.save()
        test_stage.grader = test_grader
        test_stage.save()
        contest.verification_stage = verification_stage
        contest.test_stage = test_stage
        contest.save()
        self.update(contest)
        return contest

    @transaction.atomic
    def update(self, contest):
        # these ifs are terrible, TODO change to single call
        if self.name:
            contest.name = self.name
        if self.code:
            contest.code = self.code
        if self.description:
            contest.description.from_data(self.description)
            contest.description.save()
        if self.rules:
            contest.rules.from_data(self.rules)
            contest.rules.save()
        contest.scoring_script.save_source(self.scoring_script)
        if self.verification_begin:
            contest.verification_stage.begin = self.verification_begin
        if self.verification_end:
            contest.verification_stage.end = self.verification_end
        if self.test_begin:
            contest.test_stage.begin = self.test_begin
        if self.test_end:
            contest.test_stage.end = self.test_end
        if self.published_final_results is not None:
            contest.test_stage.published_results = \
                self.published_final_results
        if self.bigger_better is not None:
            contest.bigger_better = self.bigger_better
        if self.selected_limit is not None:
            contest.test_stage.selected_limit = self.selected_limit
        contest.verification_stage.grader.save_answer(
            self.answer_for_verification)
        contest.verification_stage.grader.save()
        contest.verification_stage.save()
        contest.test_stage.grader.save_answer(self.answer_for_test)
        contest.test_stage.grader.save()
        contest.test_stage.save()
        contest.save()


class ContestStage(models.Model):
    contest = models.ForeignKey('Contest', related_name='+')
    grader = models.ForeignKey('grading.DataGrader', related_name='+')
    begin = models.DateTimeField()
    end = models.DateTimeField()
    published_results = models.BooleanField(default=False)
    requires_selection = models.BooleanField(default=False)
    selected_limit = models.IntegerField(default=-1)

    def is_open(self):
        now = timezone.now()
        return self.begin <= now <= self.end

    def __str__(self):
        return '<ContestStage %s>' % self.id


class Team(models.Model):
    name = models.CharField(max_length=100)
    contest = models.ForeignKey('Contest')

    def __repr__(self):
        return "<Team " + repr(self.name) + " in contest \"" + \
            self.contest.code + "\">"

    def __str__(self):
        return self.name


class TeamInvitation(models.Model):
    team = models.ForeignKey('Team')
    invited_by = models.ForeignKey('auth.User', null=True, related_name='+')
    secret_code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    accepted_by = models.ForeignKey('auth.User', null=True, related_name='+')

    def is_expired(self):
        latest_acceptable = self.created_at + \
            timedelta(days=settings.TEAM_INVITATION_EXPIRY)
        return timezone.now() > latest_acceptable

    def prepare(self):
        self.secret_code = User.objects.make_random_password(length=32)

    @transaction.atomic
    def accept(self, user):
        self.accepted = True
        self.accepted_by = user
        self.save()
        join_team(user, self.team)


class TeamMember(models.Model):
    team = models.ForeignKey('Team', related_name='members')
    user = models.ForeignKey('auth.User', related_name='memberships')
    contest = models.ForeignKey('Contest')

    # user can be only in one team per contest
    unique_together = ('user', 'contest')

    def __str__(self):
        return "TeamMember<%s in \"%s\" contest: \"%s\">" % \
            (self.user.username, self.team.name, self.contest.code)


def user_team(user, contest):
    if not user:
        return None
    if not user.is_authenticated():
        return None

    # Could it be simpler? I want to keep it ORM, but in SQL it is just:
    # SELECT team_id, etc FROM teams, teammembers WHERE user=:user AND
    #   teams.id = team
    membership = TeamMember.objects.select_related('team'). \
        filter(user=user, contest=contest)
    if membership.exists():
        return membership.get().team
    return None


class CannotJoin(Exception):
    pass


@transaction.atomic
def get_and_check_invitation(user, contest, team, secret_code):
    if team.contest != contest:
        raise CannotJoin("Team doesn't belong to this contest.")
    try:
        invitation = TeamInvitation.objects.get(secret_code=secret_code)
    except TeamInvitation.DoesNotExist:
        raise CannotJoin("Invalid Secret Code")
    if invitation.team != team:
        raise CannotJoin("This invitation doesn't belong to this team!")
    if invitation.is_expired():
        raise CannotJoin("This invitation is expired.")
    if invitation.accepted:
        raise CannotJoin("This invitation has already been used.")
    if not can_join_team_in_contest(user, contest):
        # TODO let the user know why exactly, like they already have team
        raise CannotJoin("Cannot join a team in this contest.")
    return invitation


@transaction.atomic
def accept_invitation(user, contest, team, secret_code):
    invitation = get_and_check_invitation(user, contest, team, secret_code)
    invitation.accept(user)


@transaction.atomic
def join_team(user, team):
    if not can_join_team_in_contest(user, team.contest):
        raise CannotJoin("Cannot join a team in this contest.")
    membership = TeamMember()
    membership.user = user
    membership.team = team
    membership.contest = team.contest
    membership.save()


def in_team(user, team):
    if not user or not user.is_authenticated():
        return False
    return TeamMember.objects.filter(team=team, user=user).exists()


def leave_team(user, team):
    if not user or not user.is_authenticated:
        return
    TeamMember.objects.filter(team=team, user=user).delete()


@transaction.atomic
def can_join_team_in_contest(user, contest):
    if not user:
        return False
    is_admin = is_contest_admin(user, contest)
    if not user.is_authenticated() or is_admin:
        return False
    has_team = TeamMember.objects.filter(contest=contest, user=user). \
        select_for_update().exists()
    return not has_team


@transaction.atomic
def can_create_team(user, contest):
    if not user:
        return False
    if not user.is_authenticated() or is_contest_admin(user, contest):
        return False
    has_team = TeamMember.objects.filter(contest=contest, user=user). \
        select_for_update().exists()
    return not has_team


class ContestSubmission(models.Model):
    stage = models.ForeignKey('ContestStage', related_name='+')
    submission = models.OneToOneField('grading.Submission')
    team = models.ForeignKey('Team', blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, default="")
    source = models.FileField(null=True, blank=True)
    selected = models.BooleanField(default=False)

    def save_source(self, source):
        if source:
            self.source.save('submission_source', source)
        elif source is False:
            self.source.delete()

    def contest(self):
        return self.stage.contest

    def created_at(self):
        return self.submission.created_at

    def __str__(self):
        return "<ContestSubmission %s>" % self.id


class ContestSubmissionEvent(models.Model):
    submission = models.OneToOneField('ContestSubmission')
    client_info = models.OneToOneField('system.ClientInfo')

    @classmethod
    def create(cls, submission, client_info):
        event = cls()
        event.submission = submission
        event.client_info = client_info
        event.save()
        return event

    def __str__(self):
        return 'ContestSubmissionEvent for %d (%s)' % \
            (self.submission.id, str(self.client_info))


class SubmissionData(object):
    output = None


class StageIsClosed(Exception):
    pass


@transaction.atomic
def submit(team, stage, submission_data):
    if team and not stage.is_open():
        raise StageIsClosed()
    cs = ContestSubmission()
    cs.stage = stage
    submission = Submission.create(stage.grader, submission_data.output)
    request_submission_grading(submission)
    submission.save()
    cs.submission = submission
    cs.team = team
    cs.save_source(submission_data.source)
    cs.comment = submission_data.comment
    cs.save()
    return cs


class SelectionError(Exception):
    pass


@transaction.atomic
def _precheck_select_submission(submission, with_lock=False):
    """
    Checks if the submission can be selected.
    Raises SelectionError if not.
    """
    if submission.selected:
        raise SelectionError("Submission is already selected.")
    if submission.team is None:
        raise SelectionError("Technical submission can't be selected.")
    if not submission.stage.is_open():
        raise SelectionError("Can't change selection in inactive contest.")
    sub_of_team_and_stage = ContestSubmission.objects.filter(
        team=submission.team,
        stage=submission.stage)
    if with_lock:
        # lock all the team's submissions in stage, (list to force evaluation)
        list(
            sub_of_team_and_stage.select_for_update().values('id', 'selected')
        )
    selected_count = sub_of_team_and_stage.filter(selected=True).count()
    limit = submission.stage.selected_limit
    if limit >= 0 and selected_count >= limit:
        raise SelectionError("Selected submissions limit reached.")


def can_select_submission(submission):
    try:
        _precheck_select_submission(submission)
    except SelectionError:
        return False
    return True


@transaction.atomic
def select_submission(submission):
    _precheck_select_submission(submission, with_lock=True)
    submission.selected = True
    submission.save()


def _precheck_unselect_submission(submission):
    if not submission.selected:
        raise SelectionError("Submission is already not selected.")
    if not submission.stage.is_open():
        raise SelectionError("Can't change selection in inactive contest.")


def can_unselect_submission(submission):
    try:
        _precheck_unselect_submission(submission)
    except SelectionError:
        return False
    return True


@transaction.atomic
def unselect_submission(submission):
    _precheck_unselect_submission(submission)
    submission.selected = False
    submission.save()


def rejudge_submission(contest_submission):
    request_submission_grading(contest_submission.submission)
    contest_submission.submission.save()


def rejudge_contest(contest):
    request_qs_grading(Submission.objects.filter(
        contestsubmission__stage__contest=contest))


def remaining_selections(team, stage):
    limit = stage.selected_limit
    if limit < 0:
        return None
    count = ContestSubmission.objects.filter(
        team=team,
        stage=stage,
        selected=True).count()
    return limit - count


def teams_with_member_list(contest):
    # Below we want to get the memebers of each team, sorted by full name.
    # We also want only one db query.
    # Maybe can be simpler?
    #
    # We have to be careful to include teams with no members.
    #
    # TOTAL_HOURS_WASTED_HERE: 1
    members = TeamMember.objects.filter(contest=contest). \
        select_related('user'). \
        order_by('user__last_name', 'user__first_name')
    team_members = dict()
    for member in members:
        if member.team_id in team_members:
            team_members[member.team_id].append(member)
        else:
            team_members[member.team_id] = [member]
    teams = Team.objects.filter(contest=contest)
    for team in teams:
        if team.id in team_members:
            team.member_list = team_members[team.id]
        else:
            team.member_list = []
    return sorted(teams, key=lambda team: team.name)


class LeadboardEntry:
    position = None
    team = None
    submission = None
    score = None

    def __repr__(self):
        return "<LeadboardEntry %s %s %s %s>" % (
            repr(self.position),
            repr(self.team),
            repr(self.submission),
            repr(self.score))


def build_leaderboard(contest, stage):
    # TODO split into multiple smaller functions, define helpers etc.
    # maybe in a separate file?
    def cmp_tuple(val):
        """
            Tuple for comparisons, making None smaller than anything.
        """
        if val is None:
            return (False, None)
        elif contest.bigger_better:
            return (True, val)
        else:
            return (True, -val)

    submissions = ContestSubmission.objects.select_related('submission'). \
        filter(stage=stage).exclude(team__isnull=True). \
        order_by('submission__created_at')
    if stage.requires_selection:
        submissions = submissions.filter(selected=True)
    teams = teams_with_member_list(contest)

    # build entries
    by_team = dict()
    for team in teams:
        entry = LeadboardEntry()
        entry.team = team
        by_team[team.id] = entry
    for submission in submissions:
        entry = by_team[submission.team_id]
        new_score = submission.submission.score
        if cmp_tuple(entry.score) < cmp_tuple(new_score):
            entry.submission = submission
            entry.score = entry.submission.submission.score

    def good_entry(entry):
        return entry.score is not None or team.member_list

    # get them into list
    entries = [entry for _, entry in by_team.items() if good_entry(entry)]

    # boundary case
    if not entries:
        return []

    # sort them
    # alphabetic order resolves draws (but position nr will be the same)
    entries = sorted(entries, key=lambda entry: entry.team.name)
    entries = sorted(
        entries,
        key=lambda entry: cmp_tuple(entry.score),
        reverse=True
    )

    # calculate teams' positions
    last = entries[0]
    entries[0].position = 1
    cur_position = 1
    for entry in entries[1:]:
        cur_position += 1
        if entry.score == last.score:
            entry.position = last.position
        else:
            entry.position = cur_position
    return entries


class ContestContext(object):
    """
    Contest and related data in the context of one user.

    It helps keeping the business logic out of the view layer.

    There is also a performance benefit:
    it lets us avoid doing the same query over and over.

    Design info:
    It is a bad idea to add any method that changes state here.
    It should stay just a read-only "view" of the contest.
    Split it to multiple classes if it grows too much.
    """
    user = None
    contest = None
    is_contest_admin = None
    can_submit = None
    can_create_team = None
    can_see_team_submissions = None
    can_see_all_submissions = None
    can_see_verification_leaderboard = None
    can_see_test_leaderboard = None
    user_team = None
    is_observing = None
    stage_names = None

    repr_attributes = [
        'user',
        'user_team',
        'contest',
        'is_contest_admin',
        'can_submit',
        'can_create_team',
        'can_see_team_submissions',
        'can_see_all_submissions',
        'can_see_verification_leaderboard',
        'can_see_test_leaderboard',
        'is_observing',
        'stage_names'
    ]

    def __init__(self, user, contest):
        self.contest = contest
        self.user = user
        # we want user to be a model - so we can query easier
        if not self.user.is_authenticated():
            self.user = None
        self.user_team = user_team(self.user, contest)
        self.is_contest_admin = is_contest_admin(self.user, contest)
        self.can_create_team = can_create_team(self.user, contest)
        self.can_see_team_submissions = self.user_team is not None
        self.can_see_all_submissions = self.is_contest_admin
        self.can_submit = self.user_team is not None or self.is_contest_admin
        self.can_see_verification_leaderboard = \
            self.can_see_stage_leaderboard(contest.verification_stage)
        self.can_see_test_leaderboard = \
            self.can_see_stage_leaderboard(contest.test_stage)
        self.is_observing = self.user and \
            contest.observing.filter(id=self.user.id).exists()
        self.stage_names = {
            contest.verification_stage.id: 'Verification',
            contest.test_stage.id: 'Final'
        }
        self.stages = [contest.verification_stage, contest.test_stage]

    def can_submit_in_stage(self, stage):
        return self.can_submit and (self.is_contest_admin or stage.is_open())

    def can_see_submission(self, submission):
        return is_contest_admin(self.user, self.contest) or \
            (submission.team is not None and submission.team == self.user_team)

    def can_see_stage_leaderboard(self, stage):
        return self.is_contest_admin or stage.published_results

    def visible_submission_result(self, submission):
        status = submission.submission.scoring_status
        if status is None:
            return 'waiting'
        if status == 'accepted':
            if self.is_contest_admin or submission.stage.published_results:
                return 'score'
            else:
                return 'accepted'
        else:
            return status

    def __repr__(self):
        result = ['<ContestContext:']
        first = True
        for attr in self.repr_attributes:
            if not first:
                result.append(', ')
            first = False
            result.append(attr + ': ' + repr(getattr(self, attr, '?')))
        result.append('>')
        return ''.join(result)
