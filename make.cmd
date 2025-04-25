@echo off
call conda activate tggw
call mypy . --strict
