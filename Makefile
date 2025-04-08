git:
	pre-commit run --all-files
	git add .
	git commit -m "push code"
	git push origin main

run:
	uvicorn src.bot_app.app:app --reload & \
	python -m gr_app.web_demo & \
	cd frontend && npm run dev
