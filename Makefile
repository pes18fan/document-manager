archive:
	tar -czf backend/ocr/dataset.tar.gz -C backend/ocr dataset

extract:
	tar -xzf backend/ocr/dataset.tar.gz -C backend/ocr

push: archive
	dvc push

pull: extract
	dvc pull

clean:
	rm -f backend/ocr/dataset.tar.gz
