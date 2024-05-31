py build.py build
if exist "build\\lib.win-amd64-cpython-312\\sliderpath.cp312-win_amd64.pyd" (
	if exist sliderpath.pyd (rm sliderpath.pyd)
	MOVE /Y "build\\lib.win-amd64-cpython-312\\sliderpath.cp312-win_amd64.pyd" .
	RENAME sliderpath.cp312-win_amd64.pyd sliderpath.pyd
	MOVE /Y sliderpath.pyd ../
)