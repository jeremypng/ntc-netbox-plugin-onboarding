"""Worker code for processing inbound OnboardingTasks.

(c) 2020 Network To Code
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging

from django_rq import job

from .choices import OnboardingFailChoices
from .choices import OnboardingStatusChoices
from .exceptions import OnboardException
from .models import OnboardingTask
from .onboard import OnboardingManager

logger = logging.getLogger("rq.worker")
logger.setLevel(logging.DEBUG)


@job("default")
def onboard_device(task_id, credentials):
    """Process a single OnboardingTask instance."""
    username = credentials.username
    password = credentials.password
    secret = credentials.secret

    ot = OnboardingTask.objects.get(id=task_id)

    logger.info("START: onboard device")
    onboarded_device = None
    try:
        if ot.ip_address:
            onboarded_device = Device.objects.get(
                primary_ip4__address__net_host=ot.ip_address
            )
    except:
        pass

    try:
        ot.status = OnboardingStatusChoices.STATUS_RUNNING
        ot.save()

        onboarding_manager = OnboardingManager(ot=ot,
                                               username=username,
                                               password=password,
                                               secret=secret)

        if onboarding_manager.created_device:
            ot.created_device = onboarding_manager.created_device

        ot.status = OnboardingStatusChoices.STATUS_SUCCEEDED
        ot.save()
        logger.info("FINISH: onboard device")
        onboarding_status = True

    except OnboardException as exc:
        if onboarded_device:
            ot.created_device = onboarded_device

        logger.error("Onboarding Error - OnboardException")
        ot.status = OnboardingStatusChoices.STATUS_FAILED
        ot.failed_reason = exc.reason
        ot.message = exc.message
        ot.save()
        onboarding_status = False

    except Exception as exc:
        if onboarded_device:
            ot.created_device = onboarded_device

        logger.error("Onboarding Error - Exception")
        logger.error(str(exc))
        ot.status = OnboardingStatusChoices.STATUS_FAILED
        ot.failed_reason = OnboardingFailChoices.FAIL_GENERAL
        ot.message = str(exc)
        ot.save()
        onboarding_status = False

    return dict(ok=onboarding_status)
