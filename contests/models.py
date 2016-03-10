import datetime

from django.db import models
from django.db import transaction
from django.utils import timezone


from system.models import PostData, Post

from base.models import ScoringScript, DataGrader, Submission, \
    request_submission_grading, request_qs_grading

class Contest(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.ForeignKey('system.Post', related_name='+')
    rules = models.ForeignKey('system.Post', related_name='+')
    scoring_script = models.ForeignKey('base.ScoringScript')
    verification_stage = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    test_stage = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    bigger_better = models.BooleanField(default=True)
    observing = models.ManyToManyField('auth.User',
        related_name='observed_contests')

def is_contest_admin(user, contest):
    return user is not None and user.is_superuser

class ContestFactory(object):
    """
    Creates and updates a contest, with all the related objects.

    It presents simple, flat interface for creating and modifying contests.
    May seem repetitive, but it is crucial to keep views clean and helps with
    tests.
    """
    #TODO "automate" some trivial parts
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
        factory.answer_for_verification = data.get('answer_for_test')
        factory.test_begin = data.get('test_begin')
        factory.test_end = data.get('test_end')
        factory.published_final_results = data.get('published_final_results')
        return factory

    @transaction.atomic
    def create(self):
        #Builds the contest structure then updates with data
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
    grader = models.ForeignKey('base.DataGrader', related_name='+')
    begin = models.DateTimeField()
    end = models.DateTimeField()
    published_results = models.BooleanField(default=False)
    requires_selection = models.BooleanField(default=False)
    selected_limit = models.IntegerField(default=-1)

    def is_open():
        now = timezone.now()
        return begin <= now <= end

class Team(models.Model):
    name = models.CharField(max_length=100)
    contest = models.ForeignKey('Contest')

class TeamMember(models.Model):
    team = models.ForeignKey('Team', related_name='members')
    user = models.ForeignKey('auth.User', related_name='memberships')
    contest = models.ForeignKey('Contest')

    # user can be only in one team per contest
    unique_together = ('user', 'contest')

def user_team(user, contest):
    if not user:
        return None
    if not user.is_authenticated():
        return None
    # admin should have team anyway
    #if is_contest_admin(user, contest):
    #    return None

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
def join_team(user, team):
    if not can_join_team(user, team):
        raise AlreadyInTeam()
    membership = TeamMember()
    membership.user = user
    membership.team = team
    membership.contest = team.contest
    membership.save()

def in_team(user, team):
    if not user.is_authenticated():
        return False
    return TeamMember.objects.filter(team=team, user=user).exists()

def leave_team(user, team):
    if not user.is_authenticated:
        return
    TeamMember.objects.filter(team=team, user=user).delete()

def can_join_team(user, team):
    if not user.is_authenticated():
        return False
    has_team = TeamMember.objects.filter(contest=team.contest, user=user). \
        select_for_update().exists()
    return not has_team

def can_create_team(user, contest):
    if not user.is_authenticated():
        return False
    has_team = TeamMember.objects.filter(contest=team.contest, user=user). \
        select_for_update().exists()
    return not has_team

class ContestSubmission(models.Model):
    stage = models.ForeignKey('ContestStage', related_name='+')
    submission = models.OneToOneField('base.Submission')
    team = models.ForeignKey('Team', blank=True, null=True)
    selected = models.BooleanField(default=False)

    def __repr__(self):
        return "ContestSubmission<%s>" % self.id

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
    cs.save()

def can_select_submission(submission):
    if submission.team is None:
        return None
    selected_count = Submission.objects.filter(selected=True,
        team=submission.team).select_for_update().count()
    return selected_count < submission.stage.selected_limit

@transaction.atomic
def select_submission(submission):
    # TODO check for race condition
    if can_select_submission(submission):
        submission.selected = True
        submission.save()
    else:
        raise PermissionDenied('Cannot select that submission')

def rejudge_submission(contest_submission):
    request_submission_grading(contest_submission.submission)
    contest_submission.submission.save()

def rejudge_contest(contest):
    request_qs_grading(Submission.objects.filter(contestsubmission__stage__contest=contest))

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
        order_by('user__first_name', 'user__last_name')
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
    return teams

class LeadboardEntry:
    position = None
    team = None
    submission = None
    score = None

def build_leaderboard(contest, stage):
    def cmp_tuple(val):
        """
            Tuple for comparisons, making None be smaller than anything.
        """
        if val is None:
            return (False, None)
        elif contest.bigger_better:
            return (True, val)
        else:
            return (True, -val)

    submissions = ContestSubmission.objects.select_related('submission'). \
        filter(stage=stage).order_by('submission__created_at')
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

    # sort them
    entries = [entry for _, entry in by_team.items()]
    # alphabetic order resolves draws (but position nr will be the same)
    entries = sorted(entries, key=lambda entry: entry.team.name)
    entries = sorted(entries, key=lambda entry: cmp_tuple(entry.submission),
        reverse=True)
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
