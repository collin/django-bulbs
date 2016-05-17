class InstantArticleRenderer():

    def __init__(self, intermediate):
        self.generate_body(intermediate)

    def generate_body(self, intermediate):
        body = ""
        for key, body in intermediate.iteritems():
            body.append(self.render_item(key, body))

        return body

    def render_item(self, key, body):
        if key == "text":
            return body
        elif key == "betty":
            return self.render_betty(body)
        elif key == "facebook":
            return self.render_facebook(body)
        elif key == "instagram":
            return self.render_instagram(body)
        elif key == "onion_video":
            return self.render_onion_video(body)
        elif key == "soundcloud":
            return self.render_soundcloud(body)
        elif key == "twitter":
            return self.render_twitter(body)
        elif key == "vimeo":
            return self.render_vimeo(body)
        elif key == "youtube":
            return self.render_youtube(body)

        else:
            raise Exception("Key not implemented")

    def render_betty(self, body):
        pass

    def render_facebook(self, body):
        pass

    def render_instagram(self, body):
        pass

    def render_onion_video(self, body):
        pass

    def render_soundcloud(self, body):
        pass

    def render_twitter(self, body):
        pass

    def render_vimeo(self, body):
        pass

    def render_youtube(self, body):
        pass
