from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from garage_admin_mcp.s3_client import GarageS3Client, S3ObjectError


def _make_client() -> GarageS3Client:
    # moto's mock_aws must already be active when the underlying boto3
    # client is constructed, not just when a call is made - so this is a
    # helper called from inside `with mock_aws():`, not a plain fixture.
    return GarageS3Client(
        endpoint_url=None,  # moto only intercepts default AWS endpoints, not arbitrary custom ones
        access_key_id="testing",
        secret_access_key="testing",
        region="us-east-1",
    )


@pytest.mark.asyncio
async def test_list_objects_returns_key_size_and_last_modified() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")
        raw.put_object(Bucket="plane", Key="hello.txt", Body=b"hello world")

        objects = await s3_client.list_objects("plane")

    assert len(objects) == 1
    assert objects[0]["key"] == "hello.txt"
    assert objects[0]["size"] == 11
    assert "last_modified" in objects[0]


@pytest.mark.asyncio
async def test_list_objects_respects_prefix() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")
        raw.put_object(Bucket="plane", Key="a/one.txt", Body=b"1")
        raw.put_object(Bucket="plane", Key="b/two.txt", Body=b"2")

        objects = await s3_client.list_objects("plane", prefix="a/")

    assert [o["key"] for o in objects] == ["a/one.txt"]


@pytest.mark.asyncio
async def test_get_object_text_returns_decoded_content() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")
        raw.put_object(Bucket="plane", Key="hello.txt", Body=b"hello world")

        text = await s3_client.get_object_text("plane", "hello.txt", max_bytes=1000)

    assert text == "hello world"


@pytest.mark.asyncio
async def test_get_object_text_truncates_long_content() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")
        raw.put_object(Bucket="plane", Key="big.txt", Body=b"x" * 100)

        text = await s3_client.get_object_text("plane", "big.txt", max_bytes=10)

    assert text.startswith("x" * 10)
    assert "truncated" in text


@pytest.mark.asyncio
async def test_get_object_text_rejects_binary_content() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")
        raw.put_object(Bucket="plane", Key="binary.dat", Body=b"\xff\xfe\x00\x01")

        with pytest.raises(S3ObjectError, match="not valid UTF-8"):
            await s3_client.get_object_text("plane", "binary.dat", max_bytes=1000)


@pytest.mark.asyncio
async def test_get_object_text_missing_key_raises_s3_object_error() -> None:
    with mock_aws():
        s3_client = _make_client()
        raw = boto3.client("s3", region_name="us-east-1")
        raw.create_bucket(Bucket="plane")

        with pytest.raises(S3ObjectError):
            await s3_client.get_object_text("plane", "does-not-exist.txt", max_bytes=1000)
