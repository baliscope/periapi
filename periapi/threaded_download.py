#!/usr/bin/env python3
"""
Periscope API for the masses

The code in this file is Copyright (c) 2015 Russell Harkanson and is available
under The MIT License as part of Pyriscope: https://github.com/rharkanson/pyriscope

Much of the code in this file is a modification of Pyriscope code. Modification done by
https://github.com/crusherw; viewable at https://github.com/rharkanson/pyriscope/pull/12
"""

from threading import Thread, Event
from queue import Queue, Empty


class ReplayDeleted(Exception):
    """Define new exception type specifically for deleted replays"""
    pass


class TasksInfo:
    """Encapsulation of task tracking (not sure why but I'm not about to refactor this)"""
    def __init__(self, name, num_tasks):
        self.name = name
        self.num_tasks = num_tasks
        self.num_tasks_complete = 0

    def is_complete(self):
        """Are all tasks complete?"""
        return self.num_tasks_complete == self.num_tasks


class Worker(Thread):
    """Subclass of Thread with modifications to detect pool starvation and deleted replays"""
    def __init__(self, thread_pool):
        Thread.__init__(self)
        self.tasks = thread_pool.tasks
        self.tasks_info = thread_pool.tasks_info
        self.stop = thread_pool.stop
        self.start()

    def run(self):
        """Thread method modified to check for conditions deleted replays can cause"""
        while not self.stop.is_set():
            try:
                # don't block forever, ...
                func, args, kargs = self.tasks.get(timeout=0.5)
            except Empty:
                # ...check periodically if we should stop
                continue

            try:
                func(*args, **kargs)
            except Exception as _:
                raise Exception("Error: ThreadPool Worker Exception: {}".format(_))

            self.tasks_info.num_tasks_complete += 1

            self.tasks.task_done()

            if self.tasks_info.is_complete():
                # stop other threads, no more work
                self.stop.set()


class ThreadPool:
    """Object to dole out tasks to threads and track their completion"""
    def __init__(self, name, num_threads, num_tasks):
        self.tasks = Queue(0)
        self.tasks_info = TasksInfo(name, num_tasks)
        self.stop = Event()
        self.workers = [Worker(self) for _ in range(num_threads)]

    def add_task(self, func, *args, **kwargs):
        """Add a task to the pool"""
        self.tasks.put((func, args, kwargs))

    def is_complete(self):
        """Check if tasks are complete"""
        return self.tasks_info.is_complete()

    def wait_completion(self):
        """Check for dead workers and finish up"""
        # If all workers quit because of errors, tasks.join()
        # will never return. Join worker threads instead.
        while self.workers:
            try:
                self.workers = [w for w in self.workers if w.is_alive()]
                for worker in self.workers:
                    # don't block forever, ...
                    worker.join(timeout=0.5)
            # ...so we can gracefully abort on Ctrl+C
            except KeyboardInterrupt:
                self.stop.set()

        if not self.stop.is_set() and not self.tasks_info.is_complete():
            raise ReplayDeleted("Replay was deleted.")
