FROM public.ecr.aws/lambda/python:3.11

# to help install scikit-surprise
RUN yum install -y gcc gcc-c++ python3-devel
RUN pip install Cython

COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY helpers.py ${LAMBDA_TASK_ROOT}
COPY recommend.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

CMD [ "lambda_function.lambda_handler" ]