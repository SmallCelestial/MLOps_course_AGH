1.1 skip
1.2 skip
1.3 

```nano ~/.aws/credentials``` + copy paste from AWS Details (AWS CLI)

1.4 skip

2.1
![2.1 image](answers_ss/2.1.png)

2.2
![2.2 image](answers_ss/2.2.png)

2.3
```python
import zipfile
from pathlib import Path
import boto3

def download_s3_file() -> None:
    bucket_name = "mlops-the-best-course"
    s3_key = "model.zip"
    local_path = Path("../downloads") / "sentiment_model.zip"

    s3 = boto3.client('s3')
    local_path.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket_name, s3_key, str(local_path))


def extract_zip(file_path: Path) -> None:
    extract_to = Path("../models")
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


if __name__ == "__main__":
    local_zip_path = Path("../downloads/sentiment_model.zip")
    download_s3_file()
    extract_zip(local_zip_path)
```

3.1

![3.1 image](answers_ss/3.1.png)

3.2

```bash
mateusz@mateusz-Inspiron-15-3525:~$ aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account id was here>
Login Succeeded
```

3.3

```bash
(MLops_homework1) mateusz@mateusz-Inspiron-15-3525:~/extra_space/studia/UMiSI/sem3/MLops/lab1/MLops_homework1$ docker tag mlops_homework1-ml-app <...>
(MLops_homework1) mateusz@mateusz-Inspiron-15-3525:~/extra_space/studia/UMiSI/sem3/MLops/lab1/MLops_homework1$ docker push <...>
The push refers to repository [<...>]
5bca33635896: Pushed 
b992a1cc1c5c: Pushed 
fddcf22fb3b5: Pushed 
2a3e4771f062: Pushed 
cc193c810c6e: Pushed 
e6c4c63db833: Pushed 
46cd1391c75e: Pushed 
7914c8f600f5: Pushed 
latest: digest: sha256:<...> size: 2003
```

![3.3 image](answers_ss/3.3.png)

4.1
![4.1 image](answers_ss/4.1.png)

4.2
![4.2 image](answers_ss/4.2.png)

4.3
![4.3.1 image](answers_ss/4.3.1.png)

![4.3.2 image](answers_ss/4.3.2.png)

4.4.1
![4.4.1 image](answers_ss/4.4.1.png)
![4.4.2 image](answers_ss/4.4.2.png)
![4.4.3 image](answers_ss/4.4.3.png)

4.4.2
![4.4.4 image](answers_ss/4.4.4.png)

4.5
![4.5.1 image](answers_ss/4.5.1.png)
![4.5.2 image](answers_ss/4.5.2.png)

4.6
![4.6.1 image](answers_ss/4.6.1.png)
![4.6.2 image](answers_ss/4.6.2.png)

4.7
![4.7.1 image](answers_ss/4.7.1.png)
![4.7.2 image](answers_ss/4.7.2.png)

5.1
![5.1 image](answers_ss/5.1.png)

5.2
![5.2 image](answers_ss/5.2.png)
![5.2.2 image](answers_ss/5.2.2.png)


5.3
![5.3 image](answers_ss/5.3.png)

5.4
![5.4 image](answers_ss/5.4.png)

6.1

```http request
POST http://applicationLoadBalancer-162032022.us-east-1.elb.amazonaws.com/predict
Content-Type: application/json

{
  "text": "I really enjoyed deploying this application on AWS."
}
```

```text
POST http://applicationLoadBalancer-162032022.us-east-1.elb.amazonaws.com/predict

HTTP/1.1 200 OK
Date: Sat, 06 Dec 2025 17:37:24 GMT
Content-Type: application/json
Content-Length: 25
Connection: keep-alive
server: uvicorn

{
  "prediction": "positive"
}
Response file saved.
> 2025-12-06T183724.200.json

Response code: 200 (OK); Time: 551ms (551 ms); Content length: 25 bytes (25 B)
```

### Automated testing 
```python
import pytest
import httpx


@pytest.fixture
def client():
    alb_dns = "http://applicationLoadBalancer-162032022.us-east-1.elb.amazonaws.com"

    with httpx.Client(base_url=alb_dns) as client:
        yield client


def test_predict_input_validation_invalid_output(client):
    response = client.post("/predict", json={"text": ""})
    data = response.json()

    assert response.status_code == 422
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert any("min_length" in str(item) for item in data["detail"])

    response = client.post("/predict", json={"text": None})
    data = response.json()

    assert response.status_code == 422
    assert "detail" in data

    response = client.post("/predict", json={"text": 123})
    data = response.json()

    assert response.status_code == 422
    assert "detail" in data


def test_predict_input_validation_valid_output(client):
    response = client.post("/predict", json={"text": "I love this movie"})
    data = response.json()

    assert response.status_code == 200
    assert "prediction" in data
    assert data["prediction"] in ("positive", "negative", "neutral")


def test_output_is_valid(client):
    response = client.post("/predict", json={"text": "I love this movie"})
    data = response.json()

    assert "prediction" in data
    assert len(data) == 1
    assert isinstance(data["prediction"], str)
```

6.1
My application didn't have a health check endpoint, so I left the default one, and I allowed 404 codes in the health check settings of the target group. (It is only for this lab. In general, I know this is bad practice.)

![6.1 image](answers_ss/6.1.png)