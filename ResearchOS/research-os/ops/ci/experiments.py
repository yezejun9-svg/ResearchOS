import os

if __name__ == '__main__':
    if os.getenv('RESEARCHOS_TASK_ID') == 'W08':
        from research import main
        raise SystemExit(main('test.experiments'))
    from evaluation import main
    raise SystemExit(main('experiments'))
