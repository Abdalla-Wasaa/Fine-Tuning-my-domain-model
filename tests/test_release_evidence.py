from scripts.verify_submission import published_asset_matches, stopped


def test_published_asset_requires_exact_digest_repository_and_publication():
    digest='a'*64
    asset={'name':'model.safetensors','digest':'sha256:'+digest,'size':123,
           'url':'https://github.com/Abdalla-Wasaa/Fine-Tuning-my-domain-model/releases/download/v-test/model.safetensors'}
    release={'draft':False,'release_tag':'v-test','assets':[asset]}
    assert published_asset_matches(release,'model.safetensors',digest)
    assert not published_asset_matches({**release,'draft':True},'model.safetensors',digest)
    assert not published_asset_matches(release,'model.safetensors','b'*64)
    asset['url']='https://example.com/model.safetensors'
    assert not published_asset_matches(release,'model.safetensors',digest)


def test_vast_explicit_stopped_container_state():
    assert stopped({'cur_state':'stopped','intended_status':'stopped','actual_status':'exited'})
    assert not stopped({'cur_state':'running','intended_status':'stopped','actual_status':'running'})
    assert not stopped({'actual_status':'exited'})
