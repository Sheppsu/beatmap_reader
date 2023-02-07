python build.py build_ext --inplace
if exist sliderpath.cp39-win_amd64.pyd (
	if exist sliderpath.pyd rm sliderpath.pyd
	RENAME sliderpath.cp39-win_amd64.pyd sliderpath.pyd
	MOVE /Y sliderpath.pyd ../
)