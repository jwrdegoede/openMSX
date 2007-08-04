// $Id$

#include "RealTime.hh"
#include "Scheduler.hh"
#include "Timer.hh"
#include "EventDistributor.hh"
#include "EventDelay.hh"
#include "Event.hh"
#include "FinishFrameEvent.hh"
#include "GlobalSettings.hh"
#include "IntegerSetting.hh"
#include "BooleanSetting.hh"
#include "ThrottleManager.hh"
#include "checked_cast.hh"
#include <cassert>

namespace openmsx {

const double             SYNC_INTERVAL = 0.08;  // s
const long long          MAX_LAG       = 200000; // us
const unsigned long long ALLOWED_LAG   =  20000; // us

RealTime::RealTime(Scheduler& scheduler,
                   EventDistributor& eventDistributor_,
                   EventDelay& eventDelay_,
                   GlobalSettings& globalSettings)
	: Schedulable(scheduler)
	, eventDistributor(eventDistributor_)
	, eventDelay(eventDelay_)
	, throttleManager(globalSettings.getThrottleManager())
	, speedSetting   (globalSettings.getSpeedSetting())
	, pauseSetting   (globalSettings.getPauseSetting())
	, powerSetting   (globalSettings.getPowerSetting())
	, emuTime(EmuTime::zero)
{
	speedSetting.attach(*this);
	throttleManager.attach(*this);
	pauseSetting.attach(*this);
	powerSetting.attach(*this);

	setSyncPoint(scheduler.getCurrentTime());

	resync();

	eventDistributor.registerEventListener(OPENMSX_FINISH_FRAME_EVENT, *this);
	eventDistributor.registerEventListener(OPENMSX_FRAME_DRAWN_EVENT,  *this);
}

RealTime::~RealTime()
{
	eventDistributor.unregisterEventListener(OPENMSX_FRAME_DRAWN_EVENT,  *this);
	eventDistributor.unregisterEventListener(OPENMSX_FINISH_FRAME_EVENT, *this);

	powerSetting.detach(*this);
	pauseSetting.detach(*this);
	throttleManager.detach(*this);
	speedSetting.detach(*this);
}

double RealTime::getRealDuration(const EmuTime& time1, const EmuTime& time2)
{
	return (time2 - time1).toDouble() * 100.0 / speedSetting.getValue();
}

EmuDuration RealTime::getEmuDuration(double realDur)
{
	return EmuDuration(realDur * speedSetting.getValue() / 100.0);
}

bool RealTime::timeLeft(unsigned long long us, const EmuTime& time)
{
	unsigned long long realDuration =
	   static_cast<unsigned long long>(getRealDuration(emuTime, time) * 1000000ULL);
	unsigned long long currentRealTime = Timer::getTime();
	return (currentRealTime + us) <
	           (idealRealTime + realDuration + ALLOWED_LAG);
}

void RealTime::sync(const EmuTime& time, bool allowSleep)
{
	if (allowSleep) {
		removeSyncPoint();
	}
	internalSync(time, allowSleep);
	if (allowSleep) {
		setSyncPoint(time + getEmuDuration(SYNC_INTERVAL));
	}
}

void RealTime::internalSync(const EmuTime& time, bool allowSleep)
{
	if (throttleManager.isThrottled()) {
		unsigned long long realDuration =
		    static_cast<unsigned long long>(
		        getRealDuration(emuTime, time) * 1000000ULL);
		idealRealTime += realDuration;
		unsigned long long currentRealTime = Timer::getTime();
		long long sleep = idealRealTime - currentRealTime;
		if (allowSleep) {
			//PRT_DEBUG("RT: want to sleep " << sleep << "us");
			sleep += static_cast<long long>(sleepAdjust);
			long long delta = 0;
			if (sleep > 0) {
				//PRT_DEBUG("RT: Sleeping for " << sleep << "us");
				Timer::sleep(sleep);
				long long slept = Timer::getTime() - currentRealTime;
				//PRT_DEBUG("RT: Realy slept for " << slept << "us");
				delta = sleep - slept;
			}
			const double ALPHA = 0.2;
			sleepAdjust = sleepAdjust * (1 - ALPHA) + delta * ALPHA;
			//PRT_DEBUG("RT: SleepAdjust: " << sleepAdjust);
		}
		if (-sleep > MAX_LAG) {
			idealRealTime = currentRealTime - MAX_LAG / 2;
		}
	}
	if (allowSleep) {
		eventDelay.sync(time);
	}

	emuTime = time;
}

void RealTime::executeUntil(const EmuTime& time, int /*userData*/)
{
	internalSync(time, true);
	setSyncPoint(time + getEmuDuration(SYNC_INTERVAL));
}

const std::string& RealTime::schedName() const
{
	static const std::string name("RealTime");
	return name;
}

bool RealTime::signalEvent(shared_ptr<const Event> event)
{
	if (event->getType() == OPENMSX_FINISH_FRAME_EVENT) {
		const FinishFrameEvent& ffe =
			checked_cast<const FinishFrameEvent&>(*event);
		if (ffe.isSkipped()) {
			// sync but don't sleep
			sync(getScheduler().getCurrentTime(), false);
		}
	} else if (event->getType() == OPENMSX_FRAME_DRAWN_EVENT) {
		// sync and possibly sleep
		sync(getScheduler().getCurrentTime(), true);
	}
	return true;
}

void RealTime::update(const Setting& /*setting*/)
{
	resync();
}

void RealTime::update(const ThrottleManager& /*throttleManager*/)
{
	resync();
}

void RealTime::resync()
{
	idealRealTime = Timer::getTime();
	sleepAdjust = 0.0;
	removeSyncPoint();
	setSyncPoint(getScheduler().getCurrentTime());
}

} // namespace openmsx
