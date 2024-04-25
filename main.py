
from utils.video_utils import read_video,write_video
from trackers.tracker import Tracker
from team_assigner.team_assigner import TeamAssigner
from player_ball_assigner.player_ball_assigner import PlayerBallAssigner
import numpy as np
import cv2
from camera_movement_estimator.camera_movement_estimator import CameraMovementEstimator
from view_transformer.view_transformer import ViewTransformer


def main():
    
    # Read video
    video_frames = read_video("input_videos/08fd33_4.mp4")

    # Initialize tracker

    tracker = Tracker("models/best.pt")
    tracks = tracker.get_object_tracks(video_frames,read_from_stub=True,stub_path='stubs/track_stubs.pkl')

    # Get object positions
    tracker.add_position_to_tracks(tracks)

    # Camera movement estimator
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(video_frames,read_from_stub=True,stub_path='stubs/camera_movement_stubs.pkl')

    camera_movement_estimator.add_adjust_positions_to_tracks(tracks,camera_movement_per_frame)

    # view transformer 
    view_transformer = ViewTransformer()
    view_transformer.add_transformed_position_to_tracks(tracks)
    


    # Interpolate Ball positions

    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])




    # Assign player teams

    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0],tracks['players'][0])

    for frame_num , player_track in enumerate(tracks['players']):
        for player_id , track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_num],track['bbox'],player_id)

            tracks['players'][frame_num][player_id]['team'] = team
            tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]


    # Assign Ball aquisition:
    player_assigner = PlayerBallAssigner()
    team_ball_control = []


    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        
        else:
            team_ball_control.append(team_ball_control[-1])
    
    team_ball_control = np.array(team_ball_control)

            
    

    # Draw output 
    # Draw object Tracks

    output_video_frames = tracker.draw_annotations(video_frames,tracks,team_ball_control)


    ## Draw camera movement
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames,camera_movement_per_frame)


    # save video
    write_video(output_video_frames,'output_videos/output_video.avi')




if __name__ == "__main__":
    main()