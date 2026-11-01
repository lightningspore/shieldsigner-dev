"""Original backup quiz, original shuffled choices, public fixtures only.

The test observes public prompt/choices solely to drive keypad selection. It
replaces no RNG, answer checking, storage or View methods except dependency init.
"""
import json,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from runtime import Runtime,install_view_dispatch
from luckfox import LuckfoxHardware
from seedsigner.models.seed import Seed
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View
from seedsigner.views.seed_views import SeedWordsBackupTestPromptView,SeedWordsBackupTestView,SeedWordsBackupTestMistakeView,SeedWordsBackupTestSuccessView,SeedWordsWarningView,SeedOptionsView,SeedFinalizeView
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start-.2
        if elapsed<0:return set()
        i=int(elapsed/.3)
        if i>=len(self.keys):
            if elapsed>len(self.keys)*.3+5:raise TimeoutError('Public backup quiz navigation stalled')
            return set()
        return {self.keys[i]} if elapsed%.3<.16 else set()
buttons=Buttons();hardware=LuckfoxHardware();runtime=Runtime(sys.argv[1],hardware.pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json');original_initialize=View._initialize
storage=SeedStorage();controller=SimpleNamespace(storage=storage,resume_main_flow=None)
plan={'mode':'correct','words':[]};quiz_prompts=0;original_run=runtime.run

def run(cls,args):
    global quiz_prompts
    if cls.__name__=='ButtonListScreen' and args.get('title','').startswith('Verify Word #'):
        quiz_prompts+=1
        index=int(args['title'].rsplit('#',1)[1])-1
        labels=[option.button_label for option in args['button_data']]
        word=plan['words'][index]
        choice=next(i for i,label in enumerate(labels) if (label!=word if plan['mode']=='wrong' else label==word))
        buttons.load(['KEY_DOWN']*choice+['KEY_PRESS'])
    return original_run(cls,args)
runtime.run=run
with tempfile.TemporaryDirectory(prefix='lvgl-backup-quiz-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    seeds=[];checks=[]
    try:
        for count,pending in ((12,True),(24,False)):
            words=['abandon']*(count-1)+(['about'] if count==12 else ['art'])
            seed=Seed(words);seeds.append(seed);plan['words']=words
            if pending:storage.set_pending_seed(seed)
            else:storage.seeds.append(seed)
            seed_arg=None if pending else seed
            for option,expected in ((1,SeedWordsWarningView),(2,SeedFinalizeView if pending else SeedOptionsView)):
                buttons.load(['KEY_DOWN']*option+['KEY_PRESS'])
                destination=SeedWordsBackupTestPromptView(seed_arg).run()
                assert destination.View_cls is expected
                assert storage.get_pending_seed() is seed if pending else seed in storage.seeds
            buttons.load(['KEY_PRESS'])
            destination=SeedWordsBackupTestPromptView(seed_arg).run()
            assert destination.View_cls is SeedWordsBackupTestView
            plan['mode']='wrong'
            destination=destination.View_cls(**destination.view_args).run()
            assert destination.View_cls is SeedWordsBackupTestMistakeView
            assert destination.view_args['confirmed_list']==[]
            wrong_index=destination.view_args['cur_index']
            buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
            destination=destination.View_cls(**destination.view_args).run()
            assert destination.View_cls is SeedWordsBackupTestView and destination.view_args['cur_index']==wrong_index
            plan['mode']='correct';confirmed=[]
            for _ in range(count):
                view=destination.View_cls(**destination.view_args)
                destination=view.run()
                assert view.cur_index not in confirmed
                if destination.View_cls is SeedWordsBackupTestView:
                    current=destination.view_args['confirmed_list']
                    assert len(current)==len(confirmed)+1 and len(set(current))==len(current)
                    assert set(confirmed).issubset(current);confirmed=list(current)
                    assert destination.view_args['seed'] is seed_arg
                else:assert destination.View_cls is SeedWordsBackupTestSuccessView
            assert destination.View_cls is SeedWordsBackupTestSuccessView
            buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
            destination=destination.View_cls(**destination.view_args).run()
            assert destination.View_cls is (SeedFinalizeView if pending else SeedOptionsView)
            if pending:
                assert storage.get_pending_seed() is seed
                buttons.load(['KEY_PRESS']);destination=destination.View_cls().run()
                assert destination.View_cls is SeedOptionsView and storage.get_pending_seed() is None
            assert seed in storage.seeds and seed.mnemonic_list==words
            checks.append(dict(words=count,pending=pending,reviewAndSkipRoutes=True,wrongAnswerDidNotConfirm=True,retryRetainedWordIndex=True,allWordsConfirmedOnce=True,pendingSentinelPreserved=True,seedStored=True))
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,checks=checks,quizPrompts=quiz_prompts,originalRandomnessAndAnswerChecks=True,originalViewsAndStorage=True,dependencyInitializationInjected=True,physicalDisplay=True,physicalButtons=False)))
    finally:
        for seed in seeds:seed.wipe()
        storage.seeds=[];storage.clear_pending_seed();View._initialize=original_initialize;restore();runtime.close();hardware.close()
